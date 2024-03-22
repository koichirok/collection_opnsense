from typing import Optional, Union
from .BaseField import BaseField
from .utils import yn_to_bool, RangedField, ListableField
from .exceptions import TypeException


class ArrayField(BaseField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._template_node = None

    @property
    def template_node(self) -> Optional[BaseField]:
        """retrieve read only template with defaults (copy of internal structure)

        Returns:
            Optional[BaseField]: _description_
        """
        # FIXME: result must be a copy of the template node
        result = self._template_node
        return result


#     /**
#      * Copy first node pointer as template node to make sure we always have a template to create new nodes from.
#      * If the first node is virtual (no source data), remove that from the list.
#      */
#     protected function actionPostLoadingEvent()
#     {
#         // always make sure there's a node to copy our structure from
#         if ($this->internalTemplateNode == null) {
#             $firstKey = array_keys($this->internalChildnodes)[0];
#             $this->internalTemplateNode = $this->internalChildnodes[$firstKey];
#             /**
#              * if first node is empty, remove reference node.
#              */
#             if ($this->internalChildnodes[$firstKey]->getInternalIsVirtual()) {
#                 unset($this->internalChildnodes[$firstKey]);
#             }
#         }
#         // init static entries when returned by getStaticChildren()
#         foreach (static::getStaticChildren() as $skey => $payload) {
#             $container_node = $this->newContainerField($this->__reference . "." . $skey, $this->internalXMLTagName);
#             $container_node->setAttributeValue("uuid", $skey);
#             $container_node->setInternalIsVirtual();
#             foreach ($this->getTemplateNode()->iterateItems() as $key => $value) {
#                 $node = clone $value;
#                 $node->setInternalReference($container_node->__reference . "." . $key);
#                 if (isset($payload[$key])) {
#                     $node->setValue($payload[$key]);
#                 }
#                 $node->markUnchanged();
#                 $container_node->addChildNode($key, $node);
#             }
#             static::$internalStaticChildren[$skey] = $container_node;
#         }
#     }


#     /**
#      * add new node containing the types from the first node (copy)
#      * @return ContainerField created node
#      * @throws \Exception
#      */
#     public function add()
#     {
#         $new_record = array();
#         foreach ($this->internalTemplateNode->iterateItems() as $key => $node) {
#             if ($node->isContainer()) {
#                 foreach ($node->iterateRecursiveItems() as $subnode) {
#                     if (is_a($subnode, "OPNsense\\Base\\FieldTypes\\ArrayField")) {
#                         // validate child nodes, nesting not supported in this version.
#                         throw new \Exception("Unsupported copy, Array doesn't support nesting.");
#                     }
#                 }
#             }
#             $new_record[$key] = clone $node;
#         }

#         $nodeUUID = $this->generateUUID();
#         $container_node = $this->newContainerField($this->__reference . "." . $nodeUUID, $this->internalXMLTagName);
#         foreach ($new_record as $key => $node) {
#             // initialize field with new internal id and defined default value
#             $node->setInternalReference($container_node->__reference . "." . $key);
#             $node->applyDefault();
#             $node->setChanged();
#             $container_node->addChildNode($key, $node);
#         }

#         // make sure we have a UUID on repeating child items
#         $container_node->setAttributeValue("uuid", $nodeUUID);

#         // add node to this object
#         $this->addChildNode($nodeUUID, $container_node);

#         return $container_node;
#     }

#     /**
#      * remove item by id (number)
#      * @param string $index index number
#      * @return bool item found/deleted
#      */
#     public function del($index)
#     {
#         if (isset($this->internalChildnodes[(string)$index])) {
#             unset($this->internalChildnodes[$index]);
#             return true;
#         } else {
#             return false;
#         }
#     }

#     /**
#      * retrieve field validators for this field type
#      * @param string|array $fieldNames sort by fieldname
#      * @param bool $descending sort descending
#      * @param int $sort_flags sorting behavior
#      * @return array
#      */
#     public function sortedBy($fieldNames, $descending = false, $sort_flags = SORT_NATURAL | SORT_FLAG_CASE)
#     {
#         // reserve at least X number of characters for every field to improve sorting of multiple fields
#         $MAX_KEY_LENGTH = 30;

#         if (empty($fieldNames)) {
#             // unsorted, just return, without any guarantee about the ordering.
#             return iterator_to_array($this->iterateItems());
#         } elseif (!is_array($fieldNames)) {
#             // fieldnames may be a list or a single item, always convert to a list
#             $fieldNames = array($fieldNames);
#         }

#         // collect sortable data as key/value store
#         $sortedData = array();
#         foreach ($this->iterateItems() as $nodeKey => $node) {
#             // populate sort key
#             $sortKey = '';
#             foreach ($fieldNames as $fieldName) {
#                 if (isset($node->internalChildnodes[$fieldName])) {
#                     if (is_numeric((string)$node->$fieldName)) {
#                         // align numeric values right for sorting, not perfect but works for integer type values
#                         $sortKey .= sprintf("%" . $MAX_KEY_LENGTH . "s,", $node->$fieldName);
#                     } else {
#                         // normal text sorting, align left
#                         $sortKey .= sprintf("%-" . $MAX_KEY_LENGTH . "s,", $node->$fieldName);
#                     }
#                 }
#             }
#             $sortKey .= $nodeKey; // prevent overwrite of duplicates
#             $sortedData[$sortKey] = $node;
#         }

#         // sort by key on ascending or descending order
#         if (!$descending) {
#             ksort($sortedData, $sort_flags);
#         } else {
#             krsort($sortedData, $sort_flags);
#         }

#         return array_values($sortedData);
#     }


#     /**
#      * @param bool $include_static include non importable static items
#      * @param array $exclude fieldnames to exclude
#      * @return array simple array set
#      */
#     public function asRecordSet($include_static = false, $exclude = [])
#     {
#         $records = [];
#         $iterator =  $include_static ? $this->iterateItems() : parent::iterateItems();
#         foreach ($iterator as $akey => $anode) {
#             $record = [];
#             foreach ($anode->iterateItems() as $tag => $node) {
#                 if (!in_array($tag, $exclude)) {
#                     $record[$tag] = (string)$node;
#                 }
#             }
#             $records[] = $record;
#         }
#         return $records;
#     }

#     /**
#      * @param array $records payload to merge
#      * @param array $keyfields search criteria
#      * @param function $data_callback inline data modification
#      * @return array exceptions
#      */
#     public function importRecordSet($records, $keyfields = [], $data_callback = null)
#     {
#         $results = ['validations' => [], 'inserted' => 0, 'updated' => 0, 'uuids' => []];
#         $records = is_array($records) ? $records : [];
#         $current = [];
#         if (!empty($keyfields)) {
#             foreach (parent::iterateItems() as $node) {
#                 $keydata = [];
#                 foreach ($keyfields as $keyfield) {
#                     $keydata[] = (string)$node->$keyfield;
#                 }
#                 $key = implode("\n", $keydata);
#                 if (isset($current[$key])) {
#                     $current[$key] = null;
#                 } else {
#                     $current[$key] = $node;
#                 }
#             }
#         }

#         foreach ($records as $idx => $record) {
#             if (is_callable($data_callback)) {
#                 $data_callback($record);
#             }
#             $keydata = [];
#             foreach ($keyfields as $keyfield) {
#                 $keydata[] = (string)$record[$keyfield] ?? '';
#             }
#             $key = implode("\n", $keydata);
#             $node = null;
#             if (isset($current[$key])) {
#                 if ($current[$key] === null) {
#                     $results['validations'][] = ['sequence' => $idx, 'message' => gettext('Duplicate key entry found')];
#                     continue;
#                 } else {
#                     $node = $current[$key];
#                 }
#             }
#             if ($node === null) {
#                 $results['inserted'] += 1;
#                 $node = $this->add();
#             } else {
#                 $results['updated'] += 1;
#             }
#             $results['uuids'][$node->getAttributes()['uuid']] = $idx;
#             foreach ($record as $fieldname => $content) {
#                 $node->$fieldname = (string)$content;
#             }
#         }
#         return $results;
#     }
# }


class AutoNumberField(BaseField, RangedField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._minimum_value = 1
        self._maximum_value = self.PHP_INT_MAX - 1
        self.validation_message = "Invalid integer value."


class BooleanField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.validation_message = "Value should be a boolean (0,1)."


class CSVListField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._separatorchar = ","
        self._select_options = {}  # []?
        self.mask = None
        self._mask_per_item = False
        self.validation_message = "List validation error."

    @property
    def mask_per_item(self) -> bool:
        return self._mask_per_item

    @mask_per_item.setter
    def mask_per_item(self, value: str):
        self._mask_per_item = yn_to_bool(value)

    @property
    def select_options(self) -> dict:
        return self._select_options

    @select_options.setter
    def select_options(self, value: Union[dict, str]):
        """set all options for this select item.
        push a key/value array type to set all options or deliver a comma-separated list with keys and optional values
        divided by a pipe | sign.
        example :    optionA|text for option A, optionB|test for option B

        Args:
            value (dict|str): key/value option list
        """
        if isinstance(value, dict):
            self._select_options.update(value)
        else:
            for option in value.split(self._separatorchar):
                if "|" in option:
                    tmp = option.split("|")
                    self._select_options[tmp[0]] = tmp[1]
                else:
                    self._select_options[option] = option


#     /**
#      * retrieve data including selection options (from setSelectOptions)
#      * @return array
#      */
#     public function getNodeData()
#     {
#         $result = array ();
#         $selectlist = explode($this->separatorchar, (string)$this);

#         foreach ($this->selectOptions as $optKey => $optValue) {
#             $result[$optKey] = array("value" => $optValue, "selected" => 0);
#         }
#         foreach ($selectlist as $optKey) {
#             if (strlen($optKey) > 0) {
#                 if (isset($result[$optKey])) {
#                     $result[$optKey]["selected"] = 1;
#                 } else {
#                     $result[$optKey] = array("value" => $optKey, "selected" => 1);
#                 }
#             }
#         }
#         return $result;
#     }


#     /**
#      * retrieve field validators for this field type
#      * @return array returns regex validator
#      */
#     public function getValidators()
#     {
#         $validators = parent::getValidators();
#         if ($this->internalValue != null && $this->internalMask != null) {
#             $validators[] = new CallbackValidator(['callback' => function ($data) {
#                 $regex_match = function ($value, $pattern) {
#                     $matches = [];
#                     preg_match(trim($pattern), $value, $matches);
#                     return isset($matches[0]) ? $matches[0] == $value : false;
#                 };
#                 if ($this->internalMaskPerItem) {
#                     $items = explode($this->separatorchar, $this->internalValue);
#                     foreach ($items as $item) {
#                         if (!$regex_match($item, $this->internalMask)) {
#                             return ["\"" . $item . "\" is invalid. " . $this->getValidationMessage()];
#                         }
#                     }
#                 } else {
#                     if (!$regex_match($this->internalValue, $this->internalMask)) {
#                         return [$this->getValidationMessage()];
#                     }
#                 }
#                 return [];
#             }]);
#         }
#         return $validators;
#     }
# }


class ContainerField(BaseField):
    pass


class EmailField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.validation_message = "Email address is invalid."


class HostnameField(BaseField, ListableField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        # IP address allowed
        self._ip_allowed = True
        # wildcard (*) enabled
        self._host_wildcard_allowed = False
        # wildcard (*.my.top.level.domain) enabled
        self._fqdn_wildcard_allowed = False
        # zone root (@) enabled
        self._zone_root_allowed = False
        # dns name as defined by RFC2181 (lifting some constraints)
        self._is_dns_name = False
        self.validation_message = "Please specify a valid IP address or hostname."

    @property
    def is_dns_name(self):
        return self._is_dns_name

    @is_dns_name.setter
    def is_dns_name(self, value: str):
        self._is_dns_name = yn_to_bool(value)

    @property
    def ip_allowed(self):
        return self._ip_allowed

    @ip_allowed.setter
    def ip_allowed(self, value: str):
        self._ip_allowed = yn_to_bool(value)

    @property
    def host_wildcard_allowed(self):
        return self._host_wildcard_allowed

    @host_wildcard_allowed.setter
    def host_wildcard_allowed(self, value: str):
        self._host_wildcard_allowed = yn_to_bool(value)

    @property
    def fqdn_wildcard_allowed(self):
        return self._fqdn_wildcard_allowed

    @fqdn_wildcard_allowed.setter
    def fqdn_wildcard_allowed(self, value: str):
        self._fqdn_wildcard_allowed = yn_to_bool(value)

    @property
    def zone_root_allowed(self):
        return self._zone_root_allowed

    @zone_root_allowed.setter
    def zone_root_allowed(self, value: str):
        self._zone_root_allowed = yn_to_bool(value)


class IPPortField(BaseField, ListableField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.field_separator = ","
        # network family (ipv4, ipv6)
        self._address_family = None
        self.validation_message = "Invalid IP-port combination."

    @property
    def address_family(self):
        return self._address_family

    @address_family.setter
    def address_family(self, value: str):
        self._address_family = value.lower().strip()


#     /**
#      * retrieve field validators for this field type
#      * @return array returns validators
#      */
#     public function getValidators()
#     {
#         $validators = parent::getValidators();
#         if ($this->internalValue != null) {
#             $validators[] = new CallbackValidator(["callback" => function ($data) {
#                 foreach ($this->internalAsList ? explode($this->internalFieldSeparator, $data) : [$data] as $value) {
#                     if ($this->internalAddressFamily == 'ipv4' || $this->internalAddressFamily == null) {
#                         $parts = explode(':', $value);
#                         if (count($parts) == 2 && Util::isIpv4Address($parts[0]) && Util::isPort($parts[1])) {
#                             continue;
#                         }
#                     }

#                     if ($this->internalAddressFamily == 'ipv6' || $this->internalAddressFamily == null) {
#                         $parts = preg_split('/\[([^\]]+)\]/', $value, -1, PREG_SPLIT_DELIM_CAPTURE | PREG_SPLIT_NO_EMPTY);
#                         if (
#                             count($parts) == 2 &&
#                             Util::isIpv6Address($parts[0]) &&
#                             str_contains($parts[1], ':') &&
#                             Util::isPort(trim($parts[1], ': '))
#                         ) {
#                             continue;
#                         }
#                     }

#                     return ["\"" . $value . "\" is invalid. " . $this->getValidationMessage()];
#                 }
#             }]);
#         }

#         return $validators;
#     }
# }


class IntegerField(BaseField, RangedField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._maximum_value = self.PHP_INT_MAX
        self._minimum_value = self.PHP_INT_MIN
        self.validation_message = "Invalid integer value."


class LegacyLinkField(BaseField):
    pass


# {
#     /**
#      * @var null source referral (e.g. root.node.item)
#      */
#     private $internalSourceLink = null;

#     /**
#      * @var bool marks if this is a data node or a container
#      */
#     protected $internalIsContainer = false;

#     /**
#      * reflect getter to (legacy) config data
#      * {@inheritdoc}
#      */
#     public function __toString()
#     {
#         if (!empty($this->internalSourceLink)) {
#             $cnf = Config::getInstance()->object();
#             foreach (explode(".", $this->internalSourceLink) as $fieldname) {
#                 if (isset($cnf->$fieldname)) {
#                     $cnf = $cnf->$fieldname;
#                 } else {
#                     $cnf = (string)null;
#                     break;
#                 }
#             }
#             return (string)$cnf;
#         }
#         return (string)null;
#     }


#     /**
#      * read only reference, keep content empty
#      * {@inheritdoc}
#      */
#     public function setValue($value)
#     {
#         return;
#     }

#     /**
#      * set source location for this node
#      * @param string $source reference like root.node.item
#      */
#     public function setSource($source)
#     {
#         $this->internalSourceLink = $source;
#     }
# }


class MacAddressField(BaseField):
    pass


#     /**
#      * @var bool marks if this is a data node or a container
#      */
#     protected $internalIsContainer = false;

#     /**
#      * @var string when multiple values could be provided at once, specify the split character
#      */
#     protected $internalFieldSeparator = ',';

#     /**
#      * @var bool when set, results are returned as list (with all options enabled)
#      */
#     protected $internalAsList = false;

#     /**
#      * trim MAC addresses
#      * @param string $value
#      */
#     public function setValue($value)
#     {
#         parent::setValue(trim($value));
#     }

#     /**
#      * get valid options, descriptions and selected value
#      * @return array
#      */
#     public function getNodeData()
#     {
#         if ($this->internalAsList) {
#             // return result as list
#             $result = array();
#             foreach (explode($this->internalFieldSeparator, $this->internalValue) as $address) {
#                 $result[$address] = array("value" => $address, "selected" => 1);
#             }
#             return $result;
#         } else {
#             // normal, single field response
#             return $this->internalValue;
#         }
#     }

#     /**
#      * select if multiple addresses may be selected at once
#      * @param $value string value Y/N
#      */
#     public function setAsList($value)
#     {
#         $this->internalAsList = trim(strtoupper($value)) == "Y";
#     }

#     /**
#      * {@inheritdoc}
#      */
#     protected function defaultValidationMessage()
#     {
#         return gettext('Invalid MAC address.');
#     }

#     /**
#      * {@inheritdoc}
#      */
#     public function getValidators()
#     {
#         $validators = parent::getValidators();
#         if ($this->internalValue != null) {
#             $validators[] = new CallbackValidator(["callback" => function ($data) {
#                 foreach ($this->internalAsList ? explode($this->internalFieldSeparator, $data) : [$data] as $address) {
#                     if (empty(filter_var($address, FILTER_VALIDATE_MAC))) {
#                         return [$this->getValidationMessage()];
#                     }
#                 }
#                 return [];
#             }
#             ]);
#         }
#         return $validators;
#     }
# }


class NetworkField(BaseField, ListableField):
    """A class to represent a NetworkField.

    This field's value must be striped and lowercased.
    """

    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._net_mask_required = False
        self._net_mask_allowed = True
        self._wildcard_enabled = True
        self._address_family = None  # ipv4 | ipv6
        self._strict = False
        self.validation_message = "Please specify a valid network segment or IP address."

    @property
    def net_mask_required(self):
        return self._net_mask_required

    @net_mask_required.setter
    def net_mask_required(self, value: str):
        self._net_mask_required = yn_to_bool(value)

    @property
    def net_mask_allowed(self):
        return self._net_mask_allowed

    @net_mask_allowed.setter
    def net_mask_allowed(self, value: str):
        self._net_mask_allowed = yn_to_bool(value)

    @property
    def address_family(self):
        return self._address_family

    @address_family.setter
    def address_family(self, value: str):
        self._address_family = value.strip().lower()

    @property
    def wildcard_enabled(self):
        return self._wildcard_enabled

    @wildcard_enabled.setter
    def wildcard_enabled(self, value: str):
        self._wildcard_enabled = yn_to_bool(value)

    @property
    def strict(self):
        return self._strict

    @strict.setter
    def strict(self, value: str):
        self._strict = yn_to_bool(value)


#     /**
#      * retrieve field validators for this field type
#      * @return array returns Text/regex validator
#      */
#     public function getValidators()
#     {
#         $validators = parent::getValidators();
#         if ($this->internalValue != null) {
#             if ($this->internalValue != "any" || $this->internalWildcardEnabled == false) {
#                 // accept any as target
#                 $validators[] = new NetworkValidator([
#                     'message' => $this->getValidationMessage(),
#                     'split' => $this->internalFieldSeparator,
#                     'netMaskRequired' => $this->internalNetMaskRequired,
#                     'netMaskAllowed' => $this->internalNetMaskAllowed,
#                     'version' => $this->internalAddressFamily,
#                     'strict' => $this->internalStrict
#                 ]);
#             }
#         }
#         return $validators;
#     }
# }


class NumericField(BaseField, RangedField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.validation_message = "Invalid numeric value."
        self._minimum_value = -99999999999999.0
        self._maximum_value = 99999999999999.0


class UrlField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.validation_message = "Invalid URL."

class UniqueIdField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.field_loaded = False


