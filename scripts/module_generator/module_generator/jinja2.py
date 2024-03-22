from typing import Union
from pathlib import Path
import re
from jinja2 import Environment, FileSystemLoader
import inflect

TEMPLATES_DIR = Path(__file__).parent.parent.joinpath("templates")


def quote_by(value: str, quote: str = "'") -> str:
    return f"{quote}{value}{quote}"


def single_quote(value: str) -> str:
    q = "'"
    return q + value.replace(q, "\\" + q) + q


def flatten(source: list) -> list:
    result = []
    for item in source:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def regex_select(source: list, pattern: Union[re.Pattern | str]) -> list:
    if isinstance(pattern, str):
        pattern = re.compile(pattern)
    return [item for item in source if pattern.match(item)]


def pluralize(value: str) -> str:
    return inflect.engine().plural(value)


def create_environment() -> Environment:
    file_loader = FileSystemLoader(TEMPLATES_DIR)
    env = Environment(loader=file_loader, keep_trailing_newline=True)
    env.filters["quote_by"] = quote_by
    env.filters["single_quote"] = single_quote
    env.filters["flatten"] = flatten
    env.filters["pluralize"] = pluralize
    env.filters["regex_select"] = regex_select
    # env.tests['match'] = lambda value, pattern: pattern.match(value)
    return env
