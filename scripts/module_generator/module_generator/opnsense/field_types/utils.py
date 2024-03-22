import re
from typing import Any
import ndebug
from .exceptions import UnsupportedOperationError

debug = ndebug.create(__name__)


def is_numeric(value: Any) -> bool:
    if isinstance(value, str):
        return value.isnumeric()
    return isinstance(value, (int, float))


def yn_to_bool(value: str) -> bool:
    return value.strip().upper() == "Y"


def translate_php_value(value: str):
    try:
        if value in {"true", "false"}:  # boolean
            return value == "true"
        elif value == "null":  # None
            return None
        elif re.match(r"^\d+$", value):  # int
            return int(value)
        elif re.match(r"^\d+\.\d+$", value):  # float
            return float(value)
        elif m := re.match(r"^\[(.*)\]$", value):
            return [translate_php_value(x) for x in m.group(1).split(",")]
        elif m := re.match(r"^(['\"])(.*)\1$", value):
            return m.group(2)
        else:
            print("WARN: Unsupported expression:", value)
    except Exception:  # pylint: disable=broad-except
        print("WARN: Failed to translate value:", value)
    return value



class RangedField:
    PHP_INT_MIN = -9223372036854775808  # for 64-bit systems
    PHP_INT_MAX = 9223372036854775807  # for 64-bit systems

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self._minimum_value = None
        self._maximum_value = None

    @property
    def minimum_value(self):
        return self._minimum_value

    @minimum_value.setter
    def minimum_value(self, value):
        self.__setattr_if_numeric("_minimum_value", value)

    @property
    def maximum_value(self):
        return self._maximum_value

    @maximum_value.setter
    def maximum_value(self, value):
        self.__setattr_if_numeric("_maximum_value", value)

    def __setattr_if_numeric(self, name, value):
        if is_numeric(value):
            setattr(self, name, value)
        else:
            raise ValueError(f"{name} must be numeric")


#     /**
#      * retrieve field validators for this field type
#      * @return array returns Text/regex validator
#      */
#     public function getValidators()
#     {
#         $validators = parent::getValidators();
#         if ($this->internalValue != null) {
#             $validators[] = new MinMaxValidator([
#                 'message' => $this->getValidationMessage(),
#                 'min' => $this->minimum_value,
#                 'max' => $this->maximum_value,
#             ]);
#             $validators[] = new Numericality(['message' => $this->getValidationMessage()]);
#         }
#         return $validators;
#     }
# }


class ListableField:
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        super().__init__(*args, **kwargs)
        self._as_list = False
        # when multiple values could be provided at once, specify the split character
        self.field_separator = None

    @property
    def as_list(self):
        return self._as_list

    @as_list.setter
    def as_list(self, value: str):
        self._as_list = yn_to_bool(value)

    def get_node_data(self):
        # Since field_types are not intended to store data and communicate with
        # the API, this method should not be called.
        raise UnsupportedOperationError("This operation is unsupported")
        # translated code from original PHP implementation. pylint: disable=unreachable
        self._value = None  # dummy variable decl.
        if self._as_list:
            result = {}
            for value in self._value.split(self.field_separator):
                result[value] = {"value": value, "selected": 1}
            return result
        else:
            return self._value


class SortedField:
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self._sorted = False

    @property
    def sorted(self):
        return self._sorted

    @sorted.setter
    def sorted(self, value: str):
        self._sortable = yn_to_bool(value)


class FilterableField:
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        self._filters = {}

    @property
    def filterable(self) -> dict:
        return self._filters

    @filterable.setter
    def filterable(self, value: dict):
        if not isinstance(value, dict):
            raise ValueError("Filters must be a dictionary")
        self._filters = value
