from .list_field_types import BaseListField
from .utils import yn_to_bool


class PortField(BaseListField):
    # list of well known services
    WELL_KNOWN_SERVICES = [
        "cvsup",
        "domain",
        "ftp",
        "hbci",
        "http",
        "https",
        "aol",
        "auth",
        "imap",
        "imaps",
        "ipsec-msft",
        "isakmp",
        "l2f",
        "ldap",
        "ms-streaming",
        "afs3-fileserver",
        "microsoft-ds",
        "ms-wbt-server",
        "wins",
        "msnp",
        "nntp",
        "ntp",
        "netbios-dgm",
        "netbios-ns",
        "netbios-ssn",
        "openvpn",
        "pop3",
        "pop3s",
        "pptp",
        "radius",
        "radius-acct",
        "avt-profile-1",
        "sip",
        "smtp",
        "igmpv3lite",
        "urd",
        "snmp",
        "snmptrap",
        "ssh",
        "nat-stun-port",
        "submission",
        "teredo",
        "telnet",
        "tftp",
        "rfb",
    ]

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._enable_well_known = False
        self._enable_ranges = False
        self._enable_alias = False

    @property
    def enable_well_known(self) -> bool:
        return self._enable_well_known

    @enable_well_known.setter
    def enable_well_known(self, value: str):
        self._enable_well_known = yn_to_bool(value)

    @property
    def enable_ranges(self) -> bool:
        return self._enable_ranges

    @enable_ranges.setter
    def enable_ranges(self, value: str):
        self._enable_ranges = yn_to_bool(value)

    @property
    def enable_alias(self) -> bool:
        return self._enable_alias

    @enable_alias.setter
    def enable_alias(self, value: str):
        self._enable_alias = yn_to_bool(value)

# /**
#  * generate validation data (list of port numbers and well know ports)
#  */
# protected function actionPostLoadingEvent()
# {
#     $setid = $this->enableWellKnown ? "1" : "0";
#     $setid .= $this->enableAlias ? "1" : "0";
#     if (empty(self::$internalCacheOptionList[$setid])) {
#         self::$internalCacheOptionList[$setid] = [];
#         if ($this->enableWellKnown) {
#             foreach (["any"] + self::$wellknownservices as $wellknown) {
#                 self::$internalCacheOptionList[$setid][(string)$wellknown] = $wellknown;
#             }
#         }
#         if ($this->enableAlias) {
#             foreach ((new Alias())->aliases->alias->iterateItems() as $alias) {
#                 if (strpos((string)$alias->type, "port") !== false) {
#                     self::$internalCacheOptionList[$setid][(string)$alias->name] = (string)$alias->name;
#                 }
#             }
#         }
#         for ($port = 1; $port <= 65535; $port++) {
#             self::$internalCacheOptionList[$setid][(string)$port] = (string)$port;
#         }
#     }
#     $this->internalOptionList = self::$internalCacheOptionList[$setid];
# }

# /**
#  * always lowercase known portnames
#  * @param string $value
#  */
# public function setValue($value)
# {
#     $tmp = trim(strtolower($value));
#     if ($this->enableWellKnown && in_array($tmp, ["any"] + self::$wellknownservices)) {
#         return parent::setValue($tmp);
#     } else {
#         return parent::setValue($value);
#     }
# }

#     /**
#      * {@inheritdoc}
#      */
#     protected function defaultValidationMessage()
#     {
#         $msg = gettext('Please specify a valid port number (1-65535).');
#         if ($this->enableWellKnown) {
#             $msg .= ' ' . sprintf(gettext('A service name is also possible (%s).'), implode(', ', self::$wellknownservices));
#         }
#         return $msg;
#     }

#     /**
#      * @return array|string|null
#      */
#     public function getNodeData()
#     {
#         // XXX: although it's not 100% clean,
#         //      when using a selector we generally would expect to return a (appendable) list of options.
#         if ($this->internalMultiSelect) {
#             return parent::getNodeData();
#         } else {
#             return (string)$this;
#         }
#     }

#     /**
#      * retrieve field validators for this field type
#      * @return array returns InclusionIn validator
#      */
#     public function getValidators()
#     {
#         if ($this->enableRanges) {
#             // add valid ranges to options
#             foreach (explode(",", $this->internalValue) as $data) {
#                 if (strpos($data, "-") !== false) {
#                     $tmp = explode('-', $data);
#                     if (count($tmp) == 2) {
#                         if (
#                             filter_var(
#                                 $tmp[0],
#                                 FILTER_VALIDATE_INT,
#                                 ['options' => ['min_range' => 1, 'max_range' => 65535]]
#                             ) !== false &&
#                             filter_var(
#                                 $tmp[1],
#                                 FILTER_VALIDATE_INT,
#                                 ['options' => ['min_range' => 1, 'max_range' => 65535]]
#                             ) !== false &&
#                             $tmp[0] < $tmp[1]
#                         ) {
#                             $this->internalOptionList[$data] = $data;
#                         }
#                     }
#                 }
#             }
#         }
#         return parent::getValidators();
#     }
# }
