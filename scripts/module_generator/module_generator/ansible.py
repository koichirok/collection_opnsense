from collections import defaultdict
from pathlib import Path
import re
from typing import Optional
from module_generator import Base, warning
from module_generator.options import Options
from module_generator.jinja2 import create_environment
from module_generator.opnsense import Plugin
from module_generator.opnsense.field_types import (
    BaseField,
    ListableField,
    AutoNumberField,
    BooleanField,
    EmailField,
    HostnameField,
    IntegerField,
    NetworkField,
    RangedField,
    UrlField,
    UniqueIdField,
    PortField,
    BaseListField,
    ModelRelationField,
    OptionField,
    VirtualIPField,
    TextField,
)
from module_generator.utils import to_snake_case, pluralize, compile_php_regex


def get_ansible_type(field: BaseField) -> tuple[str, Optional[str]]:
    types = []
    if isinstance(field, ListableField):
        if field.as_list:
            types.append("list")
    elif isinstance(field, BaseListField):
        if field.multiple:
            types.append("list")

    if isinstance(field, BooleanField):
        types.append("bool")
    elif isinstance(field, (IntegerField, AutoNumberField)):
        types.append("int")
    elif isinstance(
        field,
        (EmailField, TextField, OptionField, NetworkField, HostnameField, VirtualIPField, ModelRelationField, UrlField),
    ):
        types.append("str")
    elif isinstance(field, PortField):
        if field.enable_well_known or field.enable_ranges:
            types.append("str")
        else:
            types.append("int")
    else:
        warning(
            "Unknown field type considered as str:",
            f"field={field.get_xml_tag_name()}:",
            field.__class__.__name__,
        )
        types.append("str")
    return types[0], types[1] if len(types) > 1 else None


class ModuleTemplates(Base):
    TEMPLATE_FILENAMES = {
        "module": "modules::_tmpl_obj.py.j2",
        "module_utils::main": "module_utils::main::_tmpl.py.j2",
    }

    def __init__(self):
        super().__init__()
        self._templates = {k: None for k in self.TEMPLATE_FILENAMES}
        self._env = create_environment()

    def get_module_template(self):
        if self._templates["module"] is None:
            self._templates["module"] = self._env.get_template(self.TEMPLATE_FILENAMES["module"])
        return self._templates["module"]

    def get_module_utils_main_template(self):
        if self._templates["module_utils::main"] is None:
            self._templates["module_utils::main"] = self._env.get_template(
                self.TEMPLATE_FILENAMES["module_utils::main"]
            )
        return self._templates["module_utils::main"]


class NullDict(dict):
    pass


class ModuleSpec(Base):
    HELPER_PACKAGE = "ansible_collections.ansibleguy.opnsense.plugins.module_utils.helper"
    HELPER_MODULES = {
        "validation": f"{HELPER_PACKAGE}.validation",
    }

    def __init__(self, model: BaseField, plugin: Plugin, options: Options):
        super().__init__()
        self.model: BaseField = model
        self.plugin: Plugin = plugin
        self.module_name = None
        self.model_name = None
        self.class_name = None
        self._init_names(model, options)

        self.api = dict(Resources={})
        self._init_api(plugin.get_apis_for_model(model.get_parent_model()))
        # cache fields by type
        self.fields: dict[str, BaseField] = {}
        self.arguments_spec = options.find_module_arguments_spec(self.module_name) or {}
        self._module_arguments = {"": {}}
        self.fields_data = None
        self._imports = {}
        self._init_fields(model)

    def _init_names(self, model: BaseField, options: Options):
        name = model.get_xml_tag_name()
        if not name:
            name = model.get_reference()
        if "." in name:
            raise ValueError("Model name contains '.':", name)
        self.model_name = name
        self.module_name = model.get_parent_model().module + "_" + name
        if class_name := options.find_module_class_name(self.module_name):
            self.class_name = class_name
        else:
            self.class_name = name.title()

    def _init_fields(self, model: BaseField):
        # init field attributes
        self.fields_data = dict(
            TYPING=dict(bool=[], list=[], select=[], int=[]),
            CHANGE=[],
            ALL=[],
            ID=[],
            TRANSLATION={},
            VALIDATION=dict(INT=defaultdict(dict), STR={}, CUSTOM={}),
            RELATION={},
        )
        for _, field in model.items():
            if field.is_container():
                self.debug(f"Skipping container field {field.get_xml_tag_name()}: type={field.__class__.__name__}")
                continue
            argname, arg, spec = self.generate_module_argument(to_snake_case(field.get_xml_tag_name()), field)

            if isinstance(field, UniqueIdField) or spec.get("id"):
                self.fields_data["ID"].append(argname)

            if (
                argname == "enabled"
                and self.get_resource_api("toggle")
                and (not self.arguments_spec or (isinstance(spec, NullDict) and self.arguments_spec))
            ):
                # use "enabled" as a toggle argument if it's not a member of the module_args
                self.fields_data["TOGGLE"] = argname
                self.fields_data["ALL"].append(argname)
                self.add_module_argument(argname, arg, "toggle")
            elif not self.arguments_spec or not isinstance(spec, NullDict):
                self.fields_data["CHANGE"].append(argname)
                self.add_module_argument(argname, arg)
            else:
                self.add_module_argument(argname, arg, "unused")

            if argname in self.get_module_arguments("unused", {}):
                continue

            if argname != field.get_xml_tag_name():
                self.fields_data["TRANSLATION"][argname] = field.get_xml_tag_name()

            if "choices" in arg:
                self.fields_data["TYPING"]["select"].append(argname)
            elif arg["type"] in self.fields_data["TYPING"]:
                self.fields_data["TYPING"][arg["type"]].append(argname)

            self.build_field_validation(argname, field)
            if isinstance(field, ModelRelationField):
                print("XXX:", field.model)
                # self.fields_data["RELATION"][pluralize(argname)] = {}

            self.fields[argname] = field

        # remove empty
        self.fields_data["TYPING"] = {k: v for k, v in self.fields_data["TYPING"].items() if v}
        if ids := self.fields_data.get("ID"):
            if len(ids) == 1:
                self.fields_data["ID"] = ids[0]
                self.fields_data["CHANGE"].remove(ids[0])
            else:
                warning("NotImplemented: Multiple ID fields not implemented:", ids)

    def build_field_validation(self, argname: str, field: BaseField):
        if isinstance(field, UrlField):
            self.add_custom_import(self.HELPER_MODULES["validation"], "is_valid_url")
            self.fields_data["VALIDATION"]["CUSTOM"][argname] = "is_valid_url"
        elif isinstance(field, EmailField):
            self.add_custom_import(self.HELPER_MODULES["validation"], "is_valid_email")
            self.fields_data["VALIDATION"]["CUSTOM"][argname] = "is_valid_email"
        elif isinstance(field, HostnameField):
            if field.fqdn_wildcard_allowed:
                # additionally allowed logic: *.example.com, *.*, *
                warning("NotImplemented: HostnameField validation (fqdn_wildcard_allowed) unsupported:", argname)
            if field.zone_root_allowed:
                # additionally allowed logic: @.example.com, @, @.*
                warning("NotImplemented: HostnameField validation (zone_root_allowed) unsupported:", argname)
            if field.ip_allowed:
                # allowed pattern: IPv4 and IPv6 address
                warning("NotImplemented: HostnameField validation (ip_allowed) unsupported:", argname)
            # allowed pattern: domain name, IP addresses are not allowed
            self.add_custom_import(self.HELPER_MODULES["validation"], "is_valid_domain")
            self.fields_data["VALIDATION"]["CUSTOM"][argname] = "is_valid_domain"
        elif mask := getattr(field, "mask", None):
            if isinstance(field, TextField):
                # valid model definition, mask should be a re.Pattern
                mask = str(mask)
                if mask.startswith("re.compile("):
                    self.add_custom_import("re")
            else:
                warning(
                    f'Non-TextField type field has "mask" property. If this is not a custom field type, Model definition should be incorrect: {argname}: {field.__class__.__name__}'
                )
                if pat := compile_php_regex(mask):
                    mask = str(pat)
            self.fields_data["VALIDATION"]["STR"][argname] = mask
        elif isinstance(field, (BooleanField, TextField, OptionField)):
            # no need to validate: BooelanFiled, TextField with no mask
            # validated by "choices": OptionField
            pass
        elif isinstance(field, RangedField):
            self.fields_data["VALIDATION"]["INT"][argname] = dict(
                min=int(field.minimum_value), max=int(field.maximum_value)
            )
        else:
            warning(f"Custom validation implementaion required: {argname} ({field.__class__.__name__})")

    def generate_module_argument(self, field_name: str, field: BaseField) -> tuple[str, dict, dict]:
        argname = to_snake_case(field_name)
        spec = self.arguments_spec.get(argname, NullDict())
        desc = self.plugin.get_form_help(field) or ""
        maintype, elmtype = get_ansible_type(field)
        arg = dict(
            type=maintype,
            required=field.required,
            default=spec.get("default", field.default),
            description=[l.strip() for l in desc.rstrip(".").splitlines()],
        )
        if "name" in spec:
            arg["aliases"] = [argname]
            argname = spec["name"]

        if "aliases" in spec:
            if "aliases" in arg:
                arg["aliases"].extend(spec["aliases"])
            else:
                arg["aliases"] = spec["aliases"]

        if elmtype:
            arg["elements"] = elmtype

        if isinstance(field, OptionField):
            arg["choices"] = field.option_values.keys()

        return argname, arg, spec

    def get_custom_imports(self):
        return self._imports

    def add_custom_import(self, module: str, name: str = None):
        if module not in self._imports:
            self._imports[module] = set()
        if name is not None:
            self._imports[module].add(name)

    def get_module_arguments(self, type: str = "", default=None):  # pylint: disable=redefined-builtin
        return self._module_arguments.get(type, default)

    def get_module_argument(self, argname: str, type: str = ""):  # pylint: disable=redefined-builtin
        return self._module_arguments[type].get(argname)

    def add_module_argument(self, argname: str, argument: dict, type: str = ""):  # pylint: disable=redefined-builtin
        if type not in self._module_arguments:
            self._module_arguments[type] = {}
        self._module_arguments[type][argname] = argument

    def get_fields(self, fields_spec: list[str] = None):
        if not fields_spec:
            return self.fields
        result = {}
        for field_name in fields_spec:
            if field_name not in self.fields:
                raise ValueError(f"Field not found: {field_name}")
            result[field_name] = self.fields[field_name]
        return result

    @property
    def opnsense_module(self) -> str:
        return self.model.get_parent_model().module

    @property
    def model_filename(self) -> Path:
        return self.model.get_parent_model().model_filename

    @property
    def api_key_path(self):
        return self.model.get_reference()

    def _init_api(self, apis_by_controller: dict[str, list[dict]]):
        # First, check controller type: Service or Resource
        controller_types = {}
        for controller, apis in apis_by_controller.items():
            controller_types[controller] = defaultdict(int)
            for api in apis:
                if self.model_filename.samefile(api["model_filename"]):
                    controller_types[controller][api["type"]] += 1
                else:
                    raise ValueError(f"Model filename mismatch: {api['model_filename']} != {self.model_filename}")

        resource_api_re = re.compile(
            rf"(?:(add|del|set|toggle|search){self.class_name}|(search){pluralize(self.class_name)})\Z",
            re.IGNORECASE,
        )
        for controller, apis in apis_by_controller.items():
            if len(controller_types[controller]) == 0:
                # Not for this model
                continue
            if len(controller_types[controller]) == 1 and "Service" in controller_types[controller]:
                # if Service controller
                if "Service" not in self.api:
                    self.api["Service"] = {}
                for api in apis:
                    if api["command"] in self.api["Service"]:
                        raise RuntimeError(
                            f"Duplicate command for service: {api['command']} in {controller} and {self.api['Service'][api['command']]['controller']}"
                        )
                    self.api["Service"][api["command"]] = api
            elif controller_types[controller].get("Resources") is not None:
                for api in apis:
                    self.debug(f"API: controller={api['controller']} command={api['command']}")
                    cmd = None
                    if m := resource_api_re.match(api["command"]):
                        cmd = m.group(1) or m.group(2)
                    elif api["command"] == "get":
                        cmd = "detail"
                    elif api["command"] == "set":
                        if "set" not in self.api["Resources"]:
                            # don't overwrite setXXX command
                            cmd = "set"
                    if cmd:
                        self.api["Resources"][cmd] = api

    def get_reload_api(self, command="reconfigure"):
        return self.api["Service"].get(command, self.api["Resources"].get(command))

    def get_resource_apis(self):
        return self.api["Resources"]

    def get_resource_api(self, command):
        return self.api["Resources"].get(command)
