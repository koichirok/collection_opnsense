import pathlib as _pathlib
import re as _re
import ndebug as _ndebug
from module_generator.utils import to_snake_case
from .exceptions import TypeException
from .utils import translate_php_value as _translate_php_value, ListableField, SortedField, RangedField
from .BaseField import BaseField
from .field_types import (
    ArrayField,
    AutoNumberField,
    BooleanField,
    ContainerField,
    CSVListField,
    EmailField,
    HostnameField,
    IntegerField,
    IPPortField,
    LegacyLinkField,
    MacAddressField,
    NetworkField,
    NumericField,
    UniqueIdField,
    UrlField,
)
from .text_field_types import TextField, Base64Field, DescriptionField, UpdateOnlyTextField
from .list_field_types import (
    BaseListField,
    AuthenticationServerField,
    AuthGroupField,
    CertificateField,
    ConfigdActionsField,
    CountryField,
    InterfaceField,
    JsonKeyValueStoreField,
    ModelRelationField,
    NetworkAliasField,
    OptionField,
    VirtualIPField,
)
from .PortField import PortField
from .ProtocolField import ProtocolField

_debug = _ndebug.create(__name__)


def for_name(field_type: str, reference: str = None, tagname: str = "") -> BaseField:
    """Create a field type instance based on the field type name.

    Args:
        field_type (str): Field type name. type must be a subclass of BaseField.
        reference (str, optional): Defaults to None.
        tagname (str, optional): XML tag name. Defaults to "".

    Raises:
        TypeException: If field type not found.

    Returns:
        BaseField: created instance of field_type class.
    """
    if field_type in globals():
        type_class = globals()[field_type]
        if issubclass(type_class, BaseField):
            return type_class(reference, tagname)
    raise TypeException(f"Field type not found: {field_type}")


def load_custom_type(fully_qualifed_classname: str, model_file: str) -> type:
    classname = fully_qualifed_classname.split("\\")[-1]
    if classname in globals():
        return globals()[classname]

    types_dir = _pathlib.Path(model_file).parent.joinpath("FieldTypes")
    if not types_dir.exists():
        raise TypeException(f"Custom types directory does not exist: {types_dir}")

    file = types_dir.joinpath(f"{classname}.php")
    tp = load_custom_type_from_file(file, fully_qualifed_classname) if file.exists() else None
    for file in types_dir.glob("*.php") if tp is None else []:
        if tp := load_custom_type_from_file(file, fully_qualifed_classname):
            break
    if tp is not None:
        try:
            return globals()[classname]
        except KeyError:
            pass
    raise TypeException(f"Failed to load custom type: {fully_qualifed_classname}")


def load_custom_type_from_file(file: _pathlib.Path, fqcn: str):
    data = parse_type_php(file)
    if fqcn == f'{data.get("namespace")}\\{data.get("name")}':
        custom_class = type(data["name"], data.get("base_class", ()), data["fields"])
        globals()[data["name"]] = custom_class
        _debug(f"Custom type loaded: {custom_class}")
        return custom_class
    return None


def parse_type_php(php_file: _pathlib.Path):
    data = dict(fields={})
    with php_file.open("r") as f:
        content = f.read()
    if m := _re.search(r"\bnamespace\s+([\\a-zA-Z0-9_]+);", content):
        data["namespace"] = m.group(1)
        content = content[m.end() :]
    if m := _re.search(r"\bclass\s+([a-zA-Z0-9_]+)(?:\s+extends\s+([a-zA-Z0-9_]+))?", content):
        data["name"] = m.group(1)
        content = content[m.end() :]
        try:
            data["base_class"] = (globals()[m.group(2)],)
        except KeyError:
            raise TypeException(f"FIXME: Base class {m.group(2)} not globally available")
    if m := _re.findall(
        r"\b(?:(?:public|protected|private)\s+)?(\$[a-zA-Z_][a-zA-Z0-9_]+)\s*=\s*([^;]*);",
        content,
    ):
        for field, value in m:
            f = to_snake_case(field.lstrip("$"))
            if f.startswith("internal_"):
                f = f[8:]
            data["fields"][f] = _translate_php_value(value)
    if "name" not in data:
        raise TypeException("Failed to parse custom type")
    _debug(f"Custom type parsed: {data}")
    return data
