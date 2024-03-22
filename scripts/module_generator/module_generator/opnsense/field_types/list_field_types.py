import os
from .BaseField import BaseField
from .utils import yn_to_bool, FilterableField


class BaseListField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._option_list = {}
        self.empty_description = None
        self._multi_select = False
        self.validation_message = "Option not in list."

    @property
    def multiple(self) -> bool:
        return self._multi_select

    @multiple.setter
    def multiple(self, value: str):
        self._multi_select = "Y" == value.upper().strip()

    #     /**
    #      * get valid options, descriptions and selected value
    #      * @return array
    #      */
    #     public function getNodeData()
    #     {
    #         if (empty($this->internalEmptyDescription)) {
    #             $this->internalEmptyDescription = gettext('None');
    #         }
    #         $result = array();
    #         // if option is not required, add empty placeholder
    #         if (!$this->internalIsRequired && !$this->internalMultiSelect) {
    #             $result[""] = [
    #                 "value" => $this->internalEmptyDescription,
    #                 "selected" => empty((string)$this->internalValue) ? 1 : 0
    #             ];
    #         }

    #         // explode options
    #         $options = explode(',', $this->internalValue);
    #         foreach ($this->internalOptionList as $optKey => $optValue) {
    #             $selected = in_array($optKey, $options) ? 1 : 0;
    #             if (is_array($optValue) && isset($optValue['value'])) {
    #                 // option container (multiple attributes), passthrough.
    #                 $result[$optKey] = $optValue;
    #             } else {
    #                 // standard (string) option
    #                 $result[$optKey] = ["value" => $optValue];
    #             }
    #             $result[$optKey]["selected"] = $selected;
    #         }

    #         return $result;
    #     }

    #     /**
    #      * {@inheritdoc}
    #      */
    #     public function getValidators()
    #     {
    #         $validators = parent::getValidators();
    #         if ($this->internalValue != null) {
    #             $args = [
    #                 'domain' => array_map('strval', array_keys($this->internalOptionList)),
    #                 'message' => $this->getValidationMessage(),
    #             ];
    #             if ($this->internalMultiSelect) {
    #                 // field may contain more than one option
    #                 $validators[] = new CsvListValidator($args);
    #             } else {
    #                 // single option selection
    #                 $validators[] = new InclusionIn($args);
    #             }
    #         }
    #         return $validators;
    #     }

    #     /**
    #      * {@inheritdoc}
    #      */
    #     public function normalizeValue()
    #     {
    #         $values = [];

    #         foreach ($this->getNodeData() as $key => $node) {
    #             if ($node['selected']) {
    #                 $values[] = $key;
    #             }
    #         }

    #         $this->setValue(implode(',', $values));
    #     }
    # }
    @property
    def empty_desc(self) -> str:
        return self.empty_description

    @empty_desc.setter
    def empty_desc(self, value: str):
        self.empty_description = value


class AuthGroupField(BaseListField):
    # valid data are obtained from remote firewall
    pass


class AuthenticationServerField(BaseListField, FilterableField):
    # valid data are obtained from remote firewall
    pass


class CertificateField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._certificate_type = "cert"

        @property
        def type(self):  # pylint: disable=redefined-builtin
            return self._certificate_type

        @type.setter
        def type(self, value: str):
            val = value.lower().strip()
            if val in {"ca", "crl"}:
                self._certificate_type = val
            else:
                self._certificate_type = "cert"


#     /**
#      * generate validation data (list of certificates)
#      */
#     protected function actionPostLoadingEvent()
#     {
#         if (!isset(self::$internalStaticOptionList[$this->certificateType])) {
#             self::$internalStaticOptionList[$this->certificateType] = array();
#             $configObj = Config::getInstance()->object();
#             foreach ($configObj->{$this->certificateType} as $cert) {
#                 if ($this->certificateType == 'ca' && (string)$cert->x509_extensions == 'ocsp') {
#                     // skip ocsp signing certs
#                     continue;
#                 }
#                 self::$internalStaticOptionList[$this->certificateType][(string)$cert->refid] = (string)$cert->descr;
#             }
#             natcasesort(self::$internalStaticOptionList[$this->certificateType]);
#         }
#         $this->internalOptionList = self::$internalStaticOptionList[$this->certificateType];
#     }
# }


class ConfigdActionsField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._filters = {}

    @property
    def filters(self):
        return self._filters

    @filters.setter
    def filters(self, value):
        """
        set filters to use (in regex) per field, all tags are combined
        and cached for the next object using the same filters
        """
        if isinstance(value, dict):
            self._filters = value

    # /**
    #  * generate validation data (list of known configd actions)
    #  */
    # protected function actionPostLoadingEvent()
    # {
    #     if (!isset(self::$internalStaticOptionList[$this->internalCacheKey])) {
    #         self::$internalStaticOptionList[$this->internalCacheKey] = array();

    #         $backend = new Backend();
    #         $service_tempfile = "/tmp/configdmodelfield.data";

    #         // check configd daemon for list of available actions, cache results as long as configd is not restarted
    #         if (!file_exists($service_tempfile) || filemtime($service_tempfile) < $backend->getLastRestart()) {
    #             $response = $backend->configdRun("configd actions json", false, 20);
    #             $actions = json_decode($response, true);
    #             if (is_array($actions)) {
    #                 file_put_contents($service_tempfile, $response);
    #             } else {
    #                 $actions = array();
    #             }
    #         } else {
    #             $actions = json_decode(file_get_contents($service_tempfile), true);
    #             if (!is_array($actions)) {
    #                 $actions = array();
    #             }
    #         }

    #         foreach ($actions as $key => $value) {
    #             // use filters to determine relevance
    #             $isMatched = true;
    #             foreach ($this->internalFilters as $filterKey => $filterData) {
    #                 if (isset($value[$filterKey])) {
    #                     $fieldData = $value[$filterKey];
    #                     if (!preg_match($filterData, $fieldData)) {
    #                         $isMatched = false;
    #                     }
    #                 }
    #             }
    #             if ($isMatched) {
    #                 if (!isset($value['description']) || $value['description'] == '') {
    #                     self::$internalStaticOptionList[$this->internalCacheKey][$key] = $key;
    #                 } else {
    #                     self::$internalStaticOptionList[$this->internalCacheKey][$key] = $value['description'];
    #                 }
    #             }
    #         }
    #         natcasesort(self::$internalStaticOptionList[$this->internalCacheKey]);
    #     }
    #     $this->internalOptionList = self::$internalStaticOptionList[$this->internalCacheKey];
    # }


class CountryField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.cache_option_list = []
        # field for adding inverted items to the selection
        self._add_inverse = False

    @property
    def add_inverted(self):
        return self._add_inverse

    @add_inverted.setter
    def add_inverted(self, value: str):
        """Add inverted countries to selection (prefix !, meaning not)"""
        self._add_inverse = yn_to_bool(value)

    # /**
    #  * @return string identifying selected options
    #  */
    # private function optionSetId()
    # {
    #     return $this->internalAddInverse ? "1" : "0";
    # }

    # /**
    #  * generate validation data (list of countries)
    #  */
    # protected function actionPostLoadingEvent()
    # {
    #     $setid = $this->optionSetId();
    #     if (!isset(self::$internalCacheOptionList[$setid])) {
    #         self::$internalCacheOptionList[$setid] = [];
    #     }
    #     if (empty(self::$internalCacheOptionList[$setid])) {
    #         $filename = '/usr/local/opnsense/contrib/tzdata/iso3166.tab';
    #         $data = file_get_contents($filename);
    #         foreach (explode("\n", $data) as $line) {
    #             $line = trim($line);
    #             if (strlen($line) > 3 && substr($line, 0, 1) != '#') {
    #                 $code = substr($line, 0, 2);
    #                 $name = trim(substr($line, 2, 9999));
    #                 self::$internalCacheOptionList[$setid][$code] = $name;
    #                 if ($this->internalAddInverse) {
    #                     self::$internalCacheOptionList[$setid]["!" . $code] = $name . " (not)";
    #                 }
    #             }
    #         }
    #         natcasesort(self::$internalCacheOptionList[$setid]);
    #     }
    #     $this->internalOptionList = self::$internalCacheOptionList[$setid];
    # }


class InterfaceField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.filters = []
        self.cache_key = "*"
        self.add_parent_devices = False
        self.allow_dynamic = 0  # bool

    # /**
    #  *  collect parents for lagg interfaces
    #  *  @return array named array containing device and lagg interface
    #  */
    # private function getConfigLaggInterfaces()
    # {
    #     $physicalInterfaces = array();
    #     $configObj = Config::getInstance()->object();
    #     if (!empty($configObj->laggs)) {
    #         foreach ($configObj->laggs->children() as $key => $lagg) {
    #             if (!empty($lagg->members)) {
    #                 foreach (explode(',', $lagg->members) as $interface) {
    #                     if (!isset($physicalInterfaces[$interface])) {
    #                         $physicalInterfaces[$interface] = array();
    #                     }
    #                     $physicalInterfaces[$interface][] = (string)$lagg->laggif;
    #                 }
    #             }
    #         }
    #     }
    #     return $physicalInterfaces;
    # }

    # /**
    #  *  collect parents for VLAN interfaces
    #  *  @return array named array containing device and VLAN interfaces
    #  */
    # private function getConfigVLANInterfaces()
    # {
    #     $physicalInterfaces = array();
    #     $configObj = Config::getInstance()->object();
    #     if (!empty($configObj->vlans)) {
    #         foreach ($configObj->vlans->children() as $key => $vlan) {
    #             if (!isset($physicalInterfaces[(string)$vlan->if])) {
    #                 $physicalInterfaces[(string)$vlan->if] = array();
    #             }
    #             $physicalInterfaces[(string)$vlan->if][] = (string)$vlan->vlanif;
    #         }
    #     }
    #     return $physicalInterfaces;
    # }

    # /**
    #  * generate validation data (list of interfaces and well know ports)
    #  */
    # protected function actionPostLoadingEvent()
    # {
    #     if (!isset(self::$internalStaticOptionList[$this->internalCacheKey])) {
    #         self::$internalStaticOptionList[$this->internalCacheKey] = array();

    #         $allInterfaces = array();
    #         $allInterfacesDevices = array(); // mapping device -> interface handle (lan/wan/optX)
    #         $configObj = Config::getInstance()->object();
    #         // Iterate over all interfaces configuration and collect data
    #         if (isset($configObj->interfaces) && $configObj->interfaces->count() > 0) {
    #             foreach ($configObj->interfaces->children() as $key => $value) {
    #                 if (!$this->internalAllowDynamic && !empty($value->internal_dynamic)) {
    #                     continue;
    #                 } elseif ($this->internalAllowDynamic == 2 && !empty($value->internal_dynamic)) {
    #                     if (empty($value->ipaddr) && empty($value->ipaddrv6)) {
    #                         continue;
    #                     }
    #                 }
    #                 $allInterfaces[$key] = $value;
    #                 if (!empty($value->if)) {
    #                     $allInterfacesDevices[(string)$value->if] = $key;
    #                 }
    #             }
    #         }

    #         if ($this->internalAddParentDevices) {
    #             // collect parents for lagg/vlan interfaces
    #             $physicalInterfaces = $this->getConfigLaggInterfaces();
    #             $physicalInterfaces = array_merge($physicalInterfaces, $this->getConfigVLANInterfaces());

    #             // add unique devices
    #             foreach ($physicalInterfaces as $interface => $devices) {
    #                 // construct interface node
    #                 $interfaceNode = new \stdClass();
    #                 $interfaceNode->enable = 0;
    #                 $interfaceNode->descr = "[{$interface}]";
    #                 $interfaceNode->if = $interface;
    #                 foreach ($devices as $device) {
    #                     if (!empty($allInterfacesDevices[$device])) {
    #                         $configuredInterface = $allInterfaces[$allInterfacesDevices[$device]];
    #                         if (!empty($configuredInterface->enable)) {
    #                             // set device enabled if any member is
    #                             $interfaceNode->enable = (string)$configuredInterface->enable;
    #                         }
    #                     }
    #                 }
    #                 // only add unconfigured devices
    #                 if (empty($allInterfacesDevices[$interface])) {
    #                     $allInterfaces[$interface] = $interfaceNode;
    #                 }
    #             }
    #         }

    #         // collect this items options
    #         foreach ($allInterfaces as $key => $value) {
    #             // use filters to determine relevance
    #             $isMatched = true;
    #             foreach ($this->internalFilters as $filterKey => $filterData) {
    #                 if (isset($value->$filterKey)) {
    #                     $fieldData = $value->$filterKey;
    #                 } else {
    #                     // not found, might be a boolean.
    #                     $fieldData = "0";
    #                 }

    #                 if (!preg_match($filterData, $fieldData)) {
    #                     $isMatched = false;
    #                 }
    #             }
    #             if ($isMatched) {
    #                 self::$internalStaticOptionList[$this->internalCacheKey][$key] =
    #                     !empty($value->descr) ? (string)$value->descr : strtoupper($key);
    #             }
    #         }
    #         natcasesort(self::$internalStaticOptionList[$this->internalCacheKey]);
    #     }
    #     $this->internalOptionList = self::$internalStaticOptionList[$this->internalCacheKey];
    # }

    # private function updateInternalCacheKey()
    # {
    #     $tmp  = serialize($this->internalFilters);
    #     $tmp .= (string)$this->internalAllowDynamic;
    #     $tmp .= $this->internalAddParentDevices ? "Y" : "N";
    #     $this->internalCacheKey = md5($tmp);
    # }
    # /**
    #  * set filters to use (in regex) per field, all tags are combined
    #  * and cached for the next object using the same filters
    #  * @param $filters filters to use
    #  */
    # public function setFilters($filters)
    # {
    #     if (is_array($filters)) {
    #         $this->internalFilters = $filters;
    #         $this->updateInternalCacheKey();
    #     }
    # }

    # /**
    #  * add parent devices to the selection in case the parent has no configuration
    #  * @param $value boolean value 0/1
    #  */
    # public function setAddParentDevices($value)
    # {
    #     if (trim(strtoupper($value)) == "Y") {
    #         $this->internalAddParentDevices = true;
    #     } else {
    #         $this->internalAddParentDevices = false;
    #     }
    #     $this->updateInternalCacheKey();
    # }

    # /**
    #  * select if dynamic (hotplug) interfaces maybe selectable
    #  * @param $value Y/N/S (Yes, No, Static)
    #  */
    # public function setAllowDynamic($value)
    # {
    #     if (trim(strtoupper($value)) == "Y") {
    #         $this->internalAllowDynamic = 1;
    #     } elseif (trim(strtoupper($value)) == "S") {
    #         $this->internalAllowDynamic = 2;
    #     } else {
    #         $this->internalAllowDynamic = 0;
    #     }
    #     $this->updateInternalCacheKey();
    # }


class JsonKeyValueStoreField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._source_field = None
        self.source_file = None
        self._select_all: bool = False
        # action to send to configd to populate the provided source
        self.configd_populate_act: str = ""
        # execute configd command only when file is older then TTL (seconds)
        self.configd_populate_ttl: int = 3600
        # sort by value (default is by key)
        self.sort_by_value: bool = False

    @property
    def source_field(self):
        return self._source_field

    @source_field.setter
    def source_field(self, value: str):
        """

        Args:
            value (str): source field, pattern for source file
        Returns:
            _type_: _description_
        """
        # TODO: I'm not sure basename works as intended here even if PHP code does
        self._source_field = os.path.basename(getattr(self._get_parent_node, value))

    @property
    def select_all(self):
        return self._select_all

    @select_all.setter
    def select_all(self, value: str):
        self._select_all = yn_to_bool(value)


#     /**
#      * @param string $value set TTL for config action
#      */
#     public function setConfigdPopulateTTL($value)
#     {
#         if (is_numeric($value)) {
#             $this->internalConfigdPopulateTTL = $value;
#         }
#     }

#     /**
#      * populate selection data
#      */
#     protected function actionPostLoadingEvent()
#     {
#         if ($this->internalSourceFile != null) {
#             if ($this->internalSourceField != null) {
#                 $sourcefile = sprintf($this->internalSourceFile, $this->internalSourceField);
#             } else {
#                 $sourcefile = $this->internalSourceFile;
#             }
#             if (!empty($this->internalConfigdPopulateAct)) {
#                 if (is_file($sourcefile)) {
#                     $sourcehandle = fopen($sourcefile, "r+");
#                 } else {
#                     $sourcehandle = fopen($sourcefile, "w");
#                 }
#                 if (flock($sourcehandle, LOCK_EX)) {
#                     // execute configd action when provided
#                     $stat = fstat($sourcehandle);
#                     $muttime = $stat['size'] == 0 ? 0 : $stat['mtime'];
#                     if (time() - $muttime > $this->internalConfigdPopulateTTL) {
#                         $act = $this->internalConfigdPopulateAct;
#                         $backend = new Backend();
#                         $response = $backend->configdRun($act, false, 20);
#                         if (!empty($response) && json_decode($response) !== null) {
#                             // only store parsable results
#                             fseek($sourcehandle, 0);
#                             ftruncate($sourcehandle, 0);
#                             fwrite($sourcehandle, $response);
#                             fflush($sourcehandle);
#                         }
#                     }
#                 }
#                 flock($sourcehandle, LOCK_UN);
#                 fclose($sourcehandle);
#             }
#             if (is_file($sourcefile)) {
#                 $data = json_decode(file_get_contents($sourcefile), true);
#                 if ($data != null) {
#                     $this->internalOptionList = $data;
#                     if ($this->internalSelectAll && $this->internalValue == "") {
#                         $this->internalValue = implode(',', array_keys($this->internalOptionList));
#                     }
#                 }
#             }
#         }
#     }

#     /**
#      * change default sorting order (value vs key)
#      * @param $value boolean value Y/N
#      */
#     public function setSortByValue($value)
#     {
#         if (trim(strtoupper($value)) == "Y") {
#             $this->internalSortByValue = true;
#         } else {
#             $this->internalSortByValue = false;
#         }
#     }

#     /**
#      * get valid options, descriptions and selected value
#      * @return array
#      */
#     public function getNodeData()
#     {
#         // set sorting by key (default) or value
#         if ($this->internalSortByValue) {
#             natcasesort($this->internalOptionList);
#         } else {
#             ksort($this->internalOptionList);
#         }
#         return parent::getNodeData();
#     }

# }


class Dummy:
    pass


class ModelRelationField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        # field content should remain sort order
        self._sorted = False
        # array|null model settings to use for validation
        self._mdl_structure = None
        # selected options from the same model
        self.options_from_this_model = False
        self.cache_key = ""
        self.cache_option_list = []

    # {'source': 'OPNsense.Cron.Cron', 'items': 'jobs.job', 'display': 'description', 'filters': {'origin': '/HAProxy/'}}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'acls.acl', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'actions.action', 'display': 'name', 'filters': {'type': '/fcgi/'}}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'actions.action', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'backends.backend', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'cpus.cpu', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'errorfiles.errorfile', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'fcgis.fcgi', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'frontends.frontend', 'display': 'name', 'filters': {'bind': '/unix@/'}}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'groups.group', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'healthchecks.healthcheck', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'mailers.mailer', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'mapfiles.mapfile', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'resolvers.resolver', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'servers.server', 'display': 'name'}}
    # {'source': 'OPNsense.HAProxy.HAProxy', 'items': 'users.user', 'display': 'name'}}
    # def load_model_options(self, force=False):
    #     """load model option list
    #     Args:
    #         force (bool, optional): force option load if we already seen this model before. Defaults to False.
    #     """
    #     # only collect options once per source/filter combination, we use a static to save our unique option
    #     # combinations over the running application.
    #     #self::$internalCacheOptionList[$this->internalCacheKey] = array();
    #     for modelData in self._mdl_structure:
    #         pass
    #         # only handle valid model sources
    #         if not ('source' in modelData and 'items' in modelData and 'display' in modelData):
    #             continue
    #         # handle optional/missing classes, i.e. from plugins
    #         classname = modelData["source"].replace('.', '\\')
    #         if not "class_exists(classname)":
    #             continue
    #         if self.get_parent_model() is not None and isinstance(self.get_parent_model(), classname):
    #             # model options from the same model, use this model in stead of creating something new
    #             model_obj = self.get_parent_model()
    #             self.options_from_this_model = True
    #         else:
    #             model_obj = classname()

    #         groupKey = modelData.get('group')
    #         displayKeys = modelData['display'].split(',')
    #         displayFormat = modelData.get('display_format', "%s")
    #         groups = {}

    #         searchItems = model_obj.getNodeByReference(modelData['items'])
    #         if searchItems is not None:
    #             for _, node in searchItems.items():
    #                 descriptions = []
    #                 for displayKey in displayKeys:
    #                     if val := getattr(node, displayKey, None) is not None:
    #                         if isinstance(val, "ModelRelationField"):
    #                             descriptions.append(val.display_value())
    #                         else:
    #                             descriptions.append(str(val))
    #                     else:
    #                         descriptions.append("")
    #                 if 'uuid' not in node.getAttributes():
    #                     continue

    #                 if 'filters' in modelData['filters']:
    #                     for filterKey, filterValue in modelData['filters'].items():
    #                         fieldData = getattr(node, filterKey, "")
    #                         if not re.match(filterValue, fieldData) and fieldData is not None:
    #                             continue 2 # XXX

    #                 if groupKey is not None:
    #                     if group := getattr(node, groupKey, None) is None:
    #                         continue
    #                     group = str(group)
    #                     if group in groups: # skip duplicates
    #                         continue
    #                     groups[group] = 1

    #                 uuid = node.getAttributes()['uuid']
    #                 self::$internalCacheOptionList[$this->internalCacheKey][$uuid] = vsprintf(
    #                     $displayFormat,
    #                     $descriptions
    #                 )
    #         unset(model_obj);

    #     if (!$this->internalIsSorted) {
    #         natcasesort(self::$internalCacheOptionList[$this->internalCacheKey]);
    #     }
    # }
    # // Set for use in BaseListField->getNodeData()
    # $this->internalOptionList = self::$internalCacheOptionList[$this->internalCacheKey];

    @property
    def model(self):
        return self._mdl_structure

    @model.setter
    def model(self, value):
        """Set model as reference list, use uuid's as key"""
        # only handle dict type input
        if isinstance(value, dict):
            self._mdl_structure = value

    #     /**
    #      * get valid options, descriptions and selected value
    #      * keeps saved item sorting when internalIsSorted is set.
    #      * @return array
    #      */
    #     public function getNodeData()
    #     {
    #         if ($this->internalIsSorted) {
    #             $optKeys = array_merge(explode(',', $this->internalValue), array_keys($this->internalOptionList));
    #             $ordered_option_list = [];
    #             foreach (array_unique($optKeys) as $key) {
    #                 if (in_array($key, array_keys($this->internalOptionList))) {
    #                     $ordered_option_list[$key] = $this->internalOptionList[$key];
    #                 }
    #             }
    #             $this->internalOptionList = $ordered_option_list;
    #         }

    #         return parent::getNodeData();
    #     }

    #     /**
    #      * @return string string display value of this field
    #      */
    #     public function display_value()
    #     {
    #         $tmp = [];
    #         foreach (explode(',', $this->internalValue) as $key) {
    #             $tmp[] = $this->internalOptionList[$key] ?? '';
    #         }
    #         return implode(',', $tmp);
    #     }

    #     /**
    #      * retrieve field validators for this field type
    #      * @return array returns Text/regex validator
    #      */
    #     public function getValidators()
    #     {
    #         if ($this->internalValue != null) {
    #             // if our options come from the same model, make sure to reload the options before validating them
    #             $this->loadModelOptions($this->internalOptionsFromThisModel);
    #         }
    #         // Use validators from BaseListField, includes validations for multi-select, and single-select.
    #         return parent::getValidators();
    #     }
    # }
    @property
    def sorted(self):
        return self._sorted

    @sorted.setter
    def sorted(self, value: str):
        self._sorted = yn_to_bool(value)


class NetworkAliasField(BaseListField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        # cached collected protocols
        self.validation_message = f"{self} is not a valid source IP address or alias."

    #     public function getNodeData()
    #     {
    #         // XXX: don't use as list, only for validation
    #         return (string)$this;
    #     }

    #     /**
    #      * generate validation data (list of protocols)
    #      */
    #     protected function actionPostLoadingEvent()
    #     {
    #         if (!isset(self::$internalStaticOptionList)) {
    #             self::$internalStaticOptionList = array();
    #         }
    #         if (empty(self::$internalStaticOptionList)) {
    #             self::$internalStaticOptionList = array();
    #             // static nets
    #             self::$internalStaticOptionList['any'] = gettext('any');
    #             self::$internalStaticOptionList['(self)'] = gettext("This Firewall");
    #             // interface nets and addresses
    #             $configObj = Config::getInstance()->object();
    #             foreach ($configObj->interfaces->children() as $ifname => $ifdetail) {
    #                 $descr = htmlspecialchars(!empty($ifdetail->descr) ? $ifdetail->descr : strtoupper($ifname));
    #                 self::$internalStaticOptionList[$ifname] = $descr . " " . gettext("net");
    #                 if (!isset($ifdetail->virtual)) {
    #                     self::$internalStaticOptionList[$ifname . "ip"] = $descr . " " . gettext("address");
    #                 }
    #             }
    #             // aliases
    #             $aliasMdl = new Alias();
    #             foreach ($aliasMdl->aliases->alias->iterateItems() as $alias) {
    #                 if (strpos((string)$alias->type, "port") === false) {
    #                     self::$internalStaticOptionList[(string)$alias->name] = (string)$alias->name;
    #                 }
    #             }
    #         }
    #         $this->internalOptionList = self::$internalStaticOptionList;
    #     }

    #     /**
    #      * retrieve field validators for this field type
    #      * @return array
    #      */
    #     public function getValidators()
    #     {
    #         if (Util::isIpAddress((string)$this) || Util::isSubnet((string)$this)) {
    #             // add to option list if input is a valid network or host
    #             $this->internalOptionList[(string)$this] = (string)$this;
    #         }
    #         return parent::getValidators();
    #     }
    # }
    @BaseListField.multiple.setter
    def multiple(self, value):
        # only single items are supported by OPNsense
        raise ValueError("Unsupported feature setMultiple()")


class OptionField(BaseListField):
    @property
    def option_values(self):
        return self._option_list

    @option_values.setter
    def option_values(self, data):
        if isinstance(data, dict):
            self._option_list = {}
            # copy options to internal structure, make sure we don't copy in array structures
            for key, value in data.items():
                if not isinstance(value, list):
                    self._option_list[key] = value
                else:
                    for subkey, subvalue in value.items():
                        self._option_list[subkey] = {"value": subvalue, "optgroup": key}


class VirtualIPField(BaseListField):
    # valid data are obtained from remote firewall
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._vip_type = "*"
        self._is_legacy_key = True

    @property
    def type(self):
        return self._vip_type

    @type.setter
    def type(self, value: str):
        """set virtual ip type (carp, proxyarp, ..)

        Args:
            value (str): virtual ip type
        """
        self._vip_type = value

    @property
    def key(self):
        return self._is_legacy_key

    @key.setter
    def key(self, value: str):
        """as this field type is used to hook legacy fields and MVC ones, specify a key here.
        default it uses a legacy (subnet) key.

        Args:
            value (str): string vip type
        """
        if value.lower() == "mvc":
            self._is_legacy_key = False
