import re
import os
from typing import Any, Generator, Union, AnyStr
import xml.etree.ElementTree as ET
from module_generator.utils import to_snake_case
from module_generator.opnsense.field_types import (
    load_custom_type,
    for_name as create_field_by_name,
)
from module_generator import Base, log_v
from module_generator.opnsense.field_types import BaseField


class ModelException(Exception):
    pass


class PhpModelClass(Base):
    def __init__(self, model_filename: os.PathLike[AnyStr]):
        """Construct instance by using model file name (XML).

        PHP model class file is expected to be in the same directory as the model XML file
        and have the same name, but with a .php extension.

        Args:
            model_filename (os.PathLike[AnyStr]): Path to the model XML file

        Raises:
            FileNotFoundError: if the model class file is not found
            ModelException: if the model class file is invalid
        """
        super().__init__()
        self.__file__ = str(model_filename).removesuffix(".xml") + ".php"
        self.namespace = None
        self.name = None
        self.parent = None
        self.interfaces = None

        model_name = os.path.basename(self.__file__).removesuffix(".php")

        # Collect data from the model class file.
        if not os.path.exists(self.__file__):
            raise FileNotFoundError(f"Model class file not found: {self.__file__}")

        with open(self.__file__, encoding="utf-8") as file:
            content = file.read()
        # search namespace or class declaration
        self.debug(f"Parsing class file: {self.__file__}")

        for found in re.findall(r"\b(namespace|class)\s([^;{]+)", content):
            if found[0] == "namespace":
                self.debug(f'Found namespace: "{found[1]}"')
                self.namespace = found[1].strip()
            elif found[0] == "class":
                self.debug(f'Found class: "{found[1]}"')
                tokens = found[1].strip().split()
                if tokens[0] != model_name:
                    continue
                self.name = tokens.pop(0)
                if tokens and tokens[0] == "extends":
                    self.parent = tokens[1]
                    tokens = tokens[2:]
                if tokens and tokens.pop(0) == "implements":
                    self.interfaces = "".join(tokens).split(",")
                break
        if self.name is None:
            raise ModelException(f"Incorrect model class file: {self.__file__}")
        self.debug(
            f"Parse result: {self.namespace}\\{self.name}"
            + (f" extends {self.parent}" if self.parent else "")
            + (f" implements {', '.join(self.interfaces)}" if self.interfaces else "")
        )


class BaseModel(Base):
    def __init__(self, model_filename: str):
        """
        Construct new model type, using its own xml template

        Raises:
            ModelException: if the model xml is not found or invalid
        """
        super().__init__()
        self._php_model_class = PhpModelClass(model_filename)
        self._module_name = str(model_filename).split("/")[-2].lower()
        self._model_filename = model_filename
        self._model_xml = ET.parse(model_filename).getroot()
        if self._model_xml.tag != "model":
            raise ModelException(f"model xml {model_filename} seems to be of wrong type")
        if (elm := self._model_xml.find("mount")) is not None:
            self._mountpoint = elm.text
        else:
            raise ModelException(f"model xml {model_filename} missing mount definition")

        # internal model data structure, should contain Field type objects
        self._data = create_field_by_name("ContainerField")
        self._data.set_parent_model(self)
        # this models version number, defaults to 0.0.0 (no version)
        self._model_version = "0.0.0"

        if (elm := self._model_xml.find("version")) is not None:
            self._model_version = elm.text

        if (elm := self._model_xml.find("migration_prefix")) is not None:
            self._model_migration_prefix = elm.text

        # We've loaded the model template, now let's parse it into this object
        self.parse_xml(self._model_xml.find("items"), self._data)

        # $this->internalData->eventPostLoading();

    @property
    def name(self) -> str:
        return self._php_model_class.name

    @property
    def model_filename(self) -> str:
        return self._model_filename

    @property
    def module(self) -> str:
        return self._module_name

    @property
    def mountpoint(self) -> str:
        """place where the real data in the config.xml should live"""
        return self._mountpoint

    def parse_option_data(self, xmlnode: ET.Element) -> Union[dict, str]:
        """parse option data for model setter.

        Args:
            xmlnode (ET.Element): node to start parsing

        Returns:
            Union[dict, str]: parsed data
        """
        if len(xmlnode) == 0:
            return xmlnode.text
        else:
            result = {}
            for child in xmlnode:
                # item keys can be overwritten using value attributes
                if (value := child.get("value")) is not None:
                    item_key = value
                else:
                    item_key = child.tag
                result[item_key] = self.parse_option_data(child)
            return result

    def parse_xml(self, xml: ET.Element, internal_data: BaseField):
        """parse model to object model using types in field_types

        Args:
            xml (ET.Element): model xml data (from items section)
            internal_data (field_types.BaseField): output structure using FieldTypes,rootnode is internalData

        Raises:
            ModelException: parse error
        """
        if ref := internal_data.get_reference():
            ref_prefix = ref + "."
        else:
            ref_prefix = ""

        for elm in xml:
            tp = elm.get("type", "ContainerField")
            if "\\" in tp:
                if tp.startswith(".\\"):
                    tp = f"{self._php_model_class.namespace}\\FieldTypes{tp[1:]}"
                load_custom_type(tp, self._model_filename)
                tp = tp.split("\\")[-1]
            try:
                field = create_field_by_name(tp, ref_prefix + elm.tag, elm.tag)
            except ValueError:
                raise ModelException("class " + tp + " missing")

            field.set_parent_model(self)
            if elm.get("volatile") == "true":
                field.set_volatile()

            # now add content to this model (recursive)
            if not field.is_container():
                internal_data.add_child_node(elm.tag, field)
                for field_prop in elm:
                    # convert to pythonic attribute name (snake_case)
                    attr_name = to_snake_case(field_prop.tag)
                    attr_value = self.parse_option_data(field_prop)
                    if hasattr(field, attr_name):
                        # XXX: For array objects we will execute parseOptionData() more than needed as the
                        #      the model data itself can't change in the meantime.
                        #      e.g. setOptionValues() with a list of static options will recalculate for each item.
                        setattr(field, attr_name, attr_value)
                    else:
                        log_v(
                            "WARN: Unexpected model definition: %s(%s) does not have %s",
                            field.get_reference(),
                            field.__class__.__name__,
                            attr_name,
                        )
                        # define new attribute on the fly
                        setattr(field, attr_name, attr_value)

            else:
                # All other node types (Text,Email,...)
                self.parse_xml(elm, field)

                # add object as child to this node
            internal_data.add_child_node(elm.tag, field)

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        return super().__getattribute__(name)

    #     /**
    #      * reflect setter to internalData (ContainerField)
    #      * @param string $name property name
    #      * @param string $value property value
    #      */
    #     public function __set($name, $value)
    #     {
    #         $this->internalData->$name = $value;
    #     }

    def get_flat_nodes(self) -> dict[str, BaseField]:
        """Returns all descendant leaf nodes.

        forward to root node's get_flat_nodes

        Returns:
            dict[str, field_types.BaseField]: all descendant leaf nodes
        """
        return self._data.get_flat_nodes()

    #     /**
    #      * get nodes as array structure
    #      * @return array
    #      */
    #     public function getNodes()
    #     {
    #         return $this->internalData->getNodes();
    #     }

    #     /**
    #      * structured setter for model
    #      * @param array $data named array
    #      * @return void
    #      * @throws Exception
    #      */
    #     public function setNodes($data)
    #     {
    #         return $this->internalData->setNodes($data);
    #     }

    def items(self) -> Generator[tuple, Any, None]:
        """iterate (non virtual) child nodes

        Returns:
            [type]: [description]

        Yields:
            Generator[tuple, Any, None]: [description]
        """
        return self._data.items()

    #     /**
    #      * iterate (non virtual) child nodes recursively
    #      * @return mixed
    #      */
    #     public function iterateRecursiveItems()
    #     {
    #         return $this->internalData->iterateRecursiveItems();
    #     }

    def is_volatile(self):
        """check if the model is not persistent in the config

        Returns:
            bool: true if memory model, false if config is stored
        """
        return self._mountpoint == ":memory:"

    def is_legacy_mapper(self):
        """check if the model maps a legacy model without a container.

        check if the model maps a legacy model without a container. these should operate similar as
        regular models, but without a migration or version number (due to the lack of a container)

        Returns:
            bool:
        """
        return self._mountpoint.endswith("+") and not self._mountpoint.startswith("//")

    def to_xml(self):
        """
        render xml document from model including all parent nodes.
        (parent nodes are included to ease testing)
        """
        if self.is_volatile() or self.is_legacy_mapper():
            xml = ET.Element("root")
            self._data.add_to_xml_node(xml)
        else:
            parts = self._mountpoint.lstrip("/").split("/")
            xml = None
            while part := parts.pop():
                child = ET.Element(part)
                if xml is not None:
                    xml.append(child)
                xml = child
            self._data.add_to_xml_node(xml.find(self._mountpoint))
            # add this model's version to the newly created xml structure
            if self._model_version:
                xml.find(self._mountpoint).set("version", self._model_version)

        return xml

    def get_node_by_reference(self, reference: str):
        """find node by reference starting at the root node

        Args:
            reference (str): node reference (point separated "node.subnode.subsubnode")
        Returns:
            Optional[BaseField] field node by reference (or None if not found)
        """
        parts = reference.split(".")
        node = self._data
        while len(parts) > 0:
            child_name = parts.pop(0)
            if node.has_child(child_name):
                node = node.get_child(child_name)
            else:
                return None
        return node

#     /**
#      * set node value by name (if reference exists)
#      * @param string $reference node reference (point separated "node.subnode.subsubnode")
#      * @param string $value
#      * @return bool value saved yes/no
#      */
#     public function setNodeByReference($reference, $value)
#     {
#         $node = $this->getNodeByReference($reference);
#         if ($node != null) {
#             $node->setValue($value);
#             return true;
#         } else {
#             return false;
#         }
#     }

    def get_version(self):
        """Return model version number.

        Note: Original PHP code returns the model version number that currently used in the
        OPNsense instance.
        """
        return self._model_version
