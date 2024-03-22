from module_generator.opnsense.field_types.BaseField import BaseField
from module_generator.utils import compile_php_regex


class TextField(BaseField):
    _is_container = False

    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self._mask = None
        self.validation_message = "Text does not validate."

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value: str):
        if pattern := compile_php_regex(value):
            value = pattern
        self._mask = value


class Base64Field(TextField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.validation_message = "Invalid Base64-encoded string."
        self._mask = r"^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$"


class DescriptionField(TextField):
    def __init__(self, reference=None, tagname=""):
        super().__init__(reference, tagname)
        self.validation_message = "Description should be a string between 1 and 255 characters."
        self._mask = r"^(?:.){1,255}$"


class UpdateOnlyTextField(TextField):
    pass
    # def __str__(self):
    #     """Always return blank"""
    #     return ""

    # def set_value(self, value):
    #     """update field (if not empty)"""
    #     if value != "":
    #         super().set_value(value)
