from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from module_generator import Base
from .collect_api_endpoints import parse_api_php
from .models import BaseModel
from .field_types import BaseField


class Plugin(Base):
    def __init__(
        self,
        name: str = None,
        plugin_dir: str = None,
        models_dir: str = None,
        controllers_dir: str = None,
    ):
        """Create a new Plugin object

        Args:
            name (str, optional): name of the plugin.
            plugin_dir (str, optional): path to the plugin directory.
            models_dir (str, optional): path to the models directory.
            controllers_dir (str, optional): path to the controllers directory.

        Raises:
            TBD
        """
        super().__init__()
        if not any([plugin_dir, models_dir, controllers_dir]):
            raise ValueError("One of plugin_dir, models_dir or controllers_dir is required")
        self._name: str = name
        self._dirs: dict[str, Path] = {}
        self._init_dirs(plugin_dir, models_dir, controllers_dir)
        if self._name is None:
            self._name = self.controllers_dir.name

        if not all([plugin_dir, models_dir, controllers_dir]):
            self.debug("Following properties are automatically set:")
            if name is None:
                self.debug(f"  Plugin name: {self._name}")
            if plugin_dir is None:
                self.debug(f"  Plugin dir: {self._dirs['root']}")
            if models_dir is None:
                self.debug(f"  Models dir: {self._dirs['models']}")
            if controllers_dir is None:
                self.debug(f"  Controllers dir: {self._dirs['controllers']}")
        # dict[controller_file_name][api_command] = api
        self._apis = None
        # dict[model_file_name] = model
        self._models: dict[str, BaseModel] = None
        # dict[form_id, help_text]
        self._form_helps: dict[str, str] = None
        # cache for model items
        self._model_items = None

    def _init_dirs(self, plugin_dir: str, models_dir: str, controllers_dir: str):
        if controllers_dir is not None:
            self._dirs["controllers"] = Path(controllers_dir)
            self._name = self.controllers_dir.name
            if models_dir is None:
                self._dirs["models"] = Path(controllers_dir.replace("/controllers/", "/models/"))
            if plugin_dir is None:
                self._dirs["root"] = self.controllers_dir.parents[6]

        elif models_dir is not None:
            self._dirs["models"] = Path(models_dir)
            self._name = self.models_dir.name
            if controllers_dir is None:
                self._dirs["controllers"] = Path(models_dir.replace("/models/", "/controllers/"))
            if plugin_dir is None:
                self._dirs["root"] = self.models_dir.parents[6]

        elif plugin_dir is not None:
            self._dirs["root"] = Path(plugin_dir)
            appdir = self.root_dir.joinpath("src", "opnsense", "mvc", "app")
            dirs = dict(
                models=[d for d in appdir.glob("models/OPNsense/*") if d.is_dir()],
                controllers=[d for d in appdir.glob("controllers/OPNsense/*") if d.is_dir()],
            )
            for k, v in dirs.items():
                if len(v) == 0:
                    raise FileNotFoundError(f"No {k} directory found in {self.root_dir}")
                if len(v) == 1:
                    self._dirs[k] = v[0]
                    if self.name is None:
                        self._name = v[0].name
                    del dirs[k]
                elif self.name is not None:
                    for d in v:
                        if d.name.lower() == self.name.lower():
                            self._dirs[k] = d
                            del dirs[k]
                            break
            if len(dirs) > 0 and self.name is None:
                msg = "More than one directory found for the controllers and/or models directories."
                msg += "Please specify the plugin name or the directories explicitly."
                raise ValueError(msg)

    @property
    def name(self) -> str:
        return self._name

    @property
    def root_dir(self) -> Path:
        return self._dirs["root"]

    @property
    def models_dir(self) -> Path:
        return self._dirs["models"]

    @property
    def controllers_dir(self) -> Path:
        return self._dirs["controllers"]

    @property
    def models(self):
        if self._models is None:
            self.load_models()
        return self._models

    @property
    def apis(self):
        if len(self._apis) == 0:
            self.load_apis()
        return self._apis

    def load_models(self):
        self._models = defaultdict(dict)
        for file in self.models_dir.glob("*.xml"):
            model = BaseModel(file)
            self._models[str(file)] = model

    def load_apis(self):
        self._apis = defaultdict(dict)
        for file in self.controllers_dir.glob("Api/*.php"):
            for api in parse_api_php(str(file)):
                self._apis[file.name][api["command"]] = api

    def load_form_helps(self):
        self._form_helps = {}
        for file in self.controllers_dir.glob("forms/*.xml"):
            self.debug("Loading form help from %s", file)
            xml = ET.parse(file)
            for field in xml.getroot().findall("field"):
                field_id_elm = field.find("id")
                field_help_elm = field.find("help")
                if field_id_elm is None:
                    self.debug("Field id not found:", ET.tostring(field))
                elif field_help_elm is None:
                    self.debug("Field help not found:", ET.tostring(field))
                else:
                    field_id = field_id_elm.text
                    self._form_helps[field_id] = field_help_elm.text.strip()

    def get_form_help(self, field: BaseField):
        if self._form_helps is None:
            self.load_form_helps()
        help_text = self._form_helps.get(field.get_reference(), None)
        if help_text is None:
            key = field.get_parent_node().get_xml_tag_name() + "." + field.get_xml_tag_name()
            help_text = self._form_helps.get(key, None)
        if help_text is None:
            help_text = "No help text found"
        return help_text

    def count_apis(self):
        return sum(len(apis) for apis in self._apis.values())

    def get_apis_for_model(self, model: BaseModel):
        result = defaultdict(list)
        model_file = Path(model.model_filename)
        for controller, apis in self._apis.items():
            for api in apis.values():
                if api.get("model_filename") is not None and model_file.samefile(api.get("model_filename")):
                    result[controller].append(api)
        return result

    def list_apis(self) -> None:
        s = "="
        header = ["Method", "Module", "Controller", "Command", "Parameters", "Type"]
        col_widths = [len(h) for h in header]
        controller_types = defaultdict(dict)
        for controller, apis in self._apis.items():
            controller_types[controller] = defaultdict(int)
            for api in apis.values():
                col_widths[0] = max(col_widths[0], len(api["method"]))
                col_widths[1] = max(col_widths[1], len(api["module"]))
                col_widths[2] = max(col_widths[2], len(api["controller"]))
                col_widths[3] = max(col_widths[3], len(api["command"]))
                col_widths[4] = max(col_widths[4], len(api["parameters"]))
                col_widths[5] = max(col_widths[5], len(api["type"]))
                controller_types[controller][api["type"]] += 1

        for controller, apis in self._apis.items():
            if len(controller_types[controller]) == 1:
                print(f"# {list(controller_types[controller].keys())[0]} ({controller})")
                # omit the type if all apis in the controller are of the same type
                cols = 5
            else:
                print(f"# {controller}")
                cols = 6
            cw = col_widths[:cols]
            h = header[:cols]
            print(" ".join([h.pop(0).ljust(i) for i in cw]))
            print(" ".join([s * i for i in cw]))
            for api in apis.values():
                # fmt: off
                print(" ".join([
                    api["method"].ljust(cw[0]),
                    api["module"].ljust(cw[1]),
                    api["controller"].ljust(cw[2]),
                    api["command"].ljust(cw[3]),
                    api["parameters"].ljust(cw[4]),
                ]))  # fmt: on
            print("-" * (sum(cw) + len(cw) - 1))
            if api.get("model_filename") is not None:
                print(
                    "<<uses>>    model:",
                    self.get_model_by_file(api["model_filename"]).name,
                    f'({api["model_filename"]})',
                )
            print()

    def count_model_items(self) -> int:
        return len(self.get_model_items())

    def get_model_items(self) -> list[BaseField]:
        """Return a list of all model items (parent of leaf nodes) in the plugin"""
        if self._model_items is None:
            items = set()
            for model in self.models.values():
                items.update([n.get_parent_node() for n in model.get_flat_nodes().values()])
            self._model_items = list(items)
        return self._model_items

    def get_model_by_file(self, file: str) -> BaseModel:
        return self.models.get(file, None)

    def list_model_items(self) -> None:
        for item in self.get_model_items():
            print(item.get_reference())
