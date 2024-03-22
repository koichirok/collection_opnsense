import sys
import xml.etree.ElementTree as ET
from typing import Any, Generator, Optional
from .exceptions import TypeException
from .utils import yn_to_bool


class BaseField:
    #
    # to avoid overwriting them in instances by calling __init__
    _is_container = True

    def __init__(self, reference=None, tagname=""):
        """
        default constructor
        :param ref: direct reference to this object
        :param tagname: xml tagname to use
        """
        super().__init__()
        self._child_nodes = {}
        # constraints for this field, additional to fieldtype
        self._constraints = []
        self._parent_node: "BaseField" = None
        self._default = None
        # == API_KEY_PATH
        self._reference: str = reference
        # tag name for this object, either the last part of the reference.
        self._xml_tag_name: str = tagname
        self._required = False
        self.validation_message = "Validation failed."
        # ???
        self._is_virtual: bool = False
        self._volatile: bool = False
        self._change_case: str = None
        self._parent_model: "module_generator.opnsense.BaseModel" = None

    @property
    def default(self) -> str:
        return self._default

    @default.setter
    def default(self, value: str):
        self._default = value

    def get_reference(self):
        return self._reference

    def set_reference(self, value: str):
        """
        change internal reference, if set it can't be changed for safety purposes.
        @param $ref internal reference
        @throws Exception change exception
        """
        if not self._reference:
            self._reference = value
        else:
            raise TypeException("cannot change reference")

    def get_xml_tag_name(self):
        return self._xml_tag_name

    # def is_array_type(self) -> bool:
    #     return isinstance(self, ArrayField)

    def get_parent_model(self) -> "module_generator.opnsense.models.BaseModel":
        return self._parent_model

    def set_parent_model(self, model: "module_generator.opnsense.models.BaseModel"):
        # read only attribute, set from model
        if self._parent_model is None:
            self._parent_model = model
            if not self._reference:
                self._reference = model.name.lower()

    def get_parent_node(self) -> "BaseField":
        return self._parent_node

    def set_parent_node(self, node: "BaseField"):
        self._parent_node = node

    def is_container(self):
        return self._is_container

    def is_virtual(self):
        return self._is_virtual

    def add_child_node(self, name: str, node: "BaseField"):
        """
        Add a child node to this node.
        @param string $name property name
        @param BaseField $node content (must be of type BaseField)
        """
        self._child_nodes[name] = node
        node.set_parent_node(self)

    def items(self) -> Generator[tuple[str, "BaseField"], None, None]:
        """
        iterate (non virtual) child nodes
        """
        for name, node in self._child_nodes.items():
            if not node.is_virtual():
                yield name, node

    def iterate_recursive_items(self):
        """
        iterate all nodes recursively.
        """
        if len(self.children) == 0:
            yield self
        else:
            for node in self.items():
                for child in node.iterate_recursive_items():
                    yield child

    def __getattr__(self, name: str) -> Any:
        if "_child_nodes" in self.__dict__ and name in self._child_nodes:
            return self._child_nodes[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if "_child_nodes" in self.__dict__ and name in self._child_nodes:
            self._child_nodes[name] = value
        else:
            super().__setattr__(name, value)

    def __contains__(self, name: str) -> bool:
        if "_child_nodes" in self.__dict__ and name in self._child_nodes:
            return True
        return super().__contains__(name) if hasattr(super(), "__contains__") else False

    @property
    def children(self):
        return self._child_nodes

    def has_child(self, name: str) -> bool:
        """check for existence of child attribute"""
        return name in self._child_nodes

    def get_child(self, name: str) -> "BaseField":
        """retrieve child object"""
        return self._child_nodes.get(name)

    @property
    def required(self) -> bool:
        return self._required

    @required.setter
    def required(self, value: str):
        self._required = yn_to_bool(value)

    @property
    def constraints(self) -> list:
        return self._constraints

    @constraints.setter
    def constraints(self, constraints: dict[str, Any]):
        """set additional constraints"""
        self._constraints = constraints

    def get_constraint_by_name(self, name: str):
        """retrieve constraint objects by defined constraints name (/key)"""
        print("WARNING: constraint support not implemented", file=sys.stderr)
        return None
        # # below is tranlated code from php. BaseConstraint is not implemented
        # # pylint: disable=unreachable
        # constraint = self._constraints.get(name)
        # tp = constraint.get("type")
        # if tp in globals():
        #     if issubclass(globals()[tp], BaseConstraint):
        #         return globals()[tp](constraint, {**constraint, "name": name, "node": self})
        # return None

    #     /**
    #      * fetch all additional validators
    #      * @return array
    #      */
    #     private function getConstraintValidators()
    #     {
    #         $result = [];
    #         foreach ($this->internalConstraints as $name => $constraint) {
    #             if (!empty($constraint['reference'])) {
    #                 // handle references (should use the same level)
    #                 $parts = explode('.', $constraint['reference']);
    #                 $parentNode = $this->getParentNode();
    #                 if (count($parts) == 2) {
    #                     $tagName = $parts[0];
    #                     if (isset($parentNode->$tagName) && !$parentNode->$tagName->getInternalIsVirtual()) {
    #                         $ref_constraint = $parentNode->$tagName->getConstraintByName($parts[1]);
    #                         if ($ref_constraint != null) {
    #                             $result[] = $ref_constraint;
    #                         }
    #                     }
    #                 }
    #             } elseif (!empty($constraint['type'])) {
    #                 $constraintObj = $this->getConstraintByName($name);
    #                 if ($constraintObj != null) {
    #                     $result[] = $constraintObj;
    #                 }
    #             }
    #         }
    #         return $result;
    #     }

    #     /**
    #      * return field validators for this field
    #      * @return array returns validators for this field type (empty if none)
    #      */
    #     public function getValidators()
    #     {
    #         $validators = $this->getConstraintValidators();
    #         if ($this->isEmptyAndRequired()) {
    #             $validators[] = new PresenceOf(['message' => gettext('A value is required.')]);
    #         }
    #         return $validators;
    #     }

    #     /**
    #      * Mark this node as virtual, only used as template for structure behind it.
    #      * Used for array structures.
    #      */
    #     public function setInternalIsVirtual()
    #     {
    #         $this->internalIsVirtual = true;
    #     }

    #     /**
    #      * returns if this node is virtual, the framework uses this to determine if this node should only be used to
    #      * clone children. (using ArrayFields)
    #      * @return bool is virtual node
    #      */
    #     public function getInternalIsVirtual()
    #     {
    #         return $this->internalIsVirtual;
    #     }

    def is_volatile(self) -> bool:
        return self._volatile

    def set_volatile(self, value: bool = True):
        """Mark this node as volatile"""
        self._volatile = value

    def get_flat_nodes(self) -> dict[str, "BaseField"]:
        """
        Recursive method to flatten tree structure for easy validation, returns only leaf nodes.
        @return array named array with field type nodes, using the internal reference.
        """
        result = {}
        if len(self._child_nodes) == 0:
            return {self._reference: self}

        for _, node in self.items():
            for child_node in node.get_flat_nodes().values():
                result[child_node.get_reference()] = child_node

        return result

    # def get_nodes(self) -> dict[str, Any]:
    #     """get nodes as dict structure"""
    #     result = {}
    #     for key, node in self.items():
    #         if node.is_container():
    #             result[key] = node.get_nodes()
    #         else:
    #             result[key] = node.get_node_data()
    #     return result

    # def get_node_data(self) -> Optional[str]:
    #     """companion for getNodes, displays node content. may be overwritten for alternative presentation."""
    #         return str(self._value) # XXX

    # def set_nodes(self, data) -> None:
    #     """
    #      * update model with data returning missing repeating tag types.
    #      * @param $data array structure containing new model content
    #      * @throws Exception
    #      """
    #     # update structure with new content
    #     for key, node in self.items():
    #         if data is not None and key in data:
    #             if node.is_container():
    #                 if isinstance(data[key], list): # dict ???
    #                     node.set_nodes(data[key])
    #                 else:
    #                     raise Exception(f"Invalid  input type for {key} (configuration error?)")
    #             else:
    #                 node.set_value(data[key])

    #     # add new items to array type objects
    #     if self.is_array_type():
    #         for data_key, data_value in data.items():
    #             if not hasattr(self, data_key):
    #                 node = $this->add(); # XXX
    #                 node.set_nodes(data_value);

    def add_to_xml_node(self, node: ET.Element):
        """Add this node and its children to the supplied simplexml node pointer."""
        if not self._reference or self.is_array_type():
            # ignore tags without internal reference (root) and ArrayTypes
            subnode = node
        else:
            # if ($this->internalValue != "") {
            #     $newNodeName = $this->getInternalXMLTagName();
            #     $subnode = $node->addChild($newNodeName);
            #     $node->$newNodeName = $this->internalValue;
            # } else {
            subnode = node.append(ET.Element(self._xml_tag_name))
            # }
            # # copy attributes into xml node
            # foreach ($this->getAttributes() as $AttrKey => $AttrValue) {
            #     $subnode->addAttribute($AttrKey, $AttrValue);
            # }
        for _, field_node in self.items():
            # Virtual and volatile fields should never be persisted
            if not field_node.is_virtual() and not field_node.is_volatile():
                field_node.add_to_xml_node(subnode)

    #     /**
    #      * apply change case to this node, called by setValue
    #      */
    #     private function applyFilterChangeCase()
    #     {
    #         if (!empty($this->internalValue)) {
    #             if ($this->internalChangeCase == 'UPPER') {
    #                 $this->internalValue = strtoupper($this->internalValue);
    #             } elseif ($this->internalChangeCase == 'LOWER') {
    #                 $this->internalValue = strtolower($this->internalValue);
    #             }
    #         }
    #     }

    #     /**
    #      * normalize the internal value to allow passing validation
    #      */
    #     public function normalizeValue()
    #     {
    #         /* implemented where needed */
    #     }
    # }
    @property
    def change_case(self) -> str:
        return self._change_case

    @change_case.setter
    def change_case(self, value: Optional[str]):
        if value is not None:
            value = value.upper().strip()
        if value in {"UPPER", "LOWER"}:
            self._change_case = value
        else:
            self._change_case = None
