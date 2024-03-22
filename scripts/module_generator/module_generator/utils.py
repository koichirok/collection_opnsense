from typing import Optional
import re
import inflect


def to_snake_case(title_or_camel_case):
    tmp = re.sub(r"\B([A-Z][^A-Z0-9])", r"_\1", title_or_camel_case)
    tmp = re.sub(r"\B([A-Z][A-Z0-9]+)", r"_\1", tmp)
    return tmp.replace("-", "_").lower()


def pluralize(value: str) -> str:
    return inflect.engine().plural(value)


def compile_php_regex(string) -> Optional[re.Pattern | str]:
    if m := re.match(r"/(.*)/([imsxeuUDAJ]*)\Z", string):
        if re.match(r"[eUDAJ]", m.group(2)):
            return string
        flags = 0
        for c in m.group(2):
            flags |= dict(i=re.I, m=re.M, s=re.S, x=re.X, u=re.U).get(c)
        pattern = re.sub(r"\\x{([0-9a-f]+)}", lambda m: f"\\u{m.group(1)}", m.group(1), flags=re.I)
        try:
            return re.compile(rf"{pattern}", flags)
        except re.error as e:
            print(f"An error occurred: {e}: {pattern}")
            raise
    return None
