from argparse import ArgumentParser, Action
import json
import logging
import re
import yaml
import ndebug
from module_generator import Base, logger

debug = ndebug.create(__name__)

class SetVerbosityAction(Action, Base):
    def __init__(self, option_strings, dest="verbose", nargs=0, **kwargs):
        Action.__init__(self, option_strings, dest, nargs=nargs, **kwargs)
        Base.__init__(self)

    def __call__(self, parser, namespace, values, option_string=None):
        val = min(getattr(namespace, self.dest, self.default) + 1, 5) if self.const is None else self.const
        setattr(namespace, self.dest, val)

def create_argument_parser():
    p = ArgumentParser(
        prog="module_generator",
        description="Generate Ansible modules from OPNsense plugin",
        # fmt: off
        usage=("\n" + " " * 7).join([
            "%(prog)s -p <DIR> [other options...]",
            "%(prog)s -m <DIR> [other options...]",
            "%(prog)s -c <DIR> [other options...]",
            "%(prog)s -h",
        ]),
        # fmt: on
    )
    p.add_argument("-d", "--dest-dir", metavar="DIR", default="dest", help="Root directory for output files")
    p.add_argument("-n", "--plugin-name", metavar="NAME", help="Name of the plugin")
    p.add_argument("-p", "--plugin-dir", metavar="DIR", help="Path to the plugin directory")
    p.add_argument("-m", "--models-dir", metavar="DIR", help="Path to the models directory")
    p.add_argument("-c", "--controllers_dir", metavar="DIR", help="Path to the controllers directory")
    p.add_argument("-v", "--verbose", action=SetVerbosityAction, default=0, help="Verbose output")
    p.add_argument("-D", "--debug", action=SetVerbosityAction, const=4, help="Debug output. Equivalent to -vvvv")
    p.add_argument("-q", "--quiet", action=SetVerbosityAction, const=-1, help="Quiet output")
    # p.add_argument("--full-debug", action=VerbosityAction, help="Full debug output. Equivalent to -vvvvv")
    g = p.add_argument_group("Module options", "Options to control the module generation")
    p.add_argument("--modules", metavar="MODULE[,MODULE...]", help="List of modules to generate")
    p.add_argument("--modules-exclude", metavar="MODULE[,MODULE...]", help="List of modules not to generate")
    p.add_argument(
        "--module-arguments",
        action="append",
        default=[],
        # fmt: off
        help="specify fields used in the module and their definition orders and their aliases in forms of: module_name:field1[field_properties],field2,..."
                "field_properties: name=alternative_field_name,aliases=[comma separated list of aliases]"
                "e.g. unbound_dot:domain[aliases=[dom,d]],server[name=target,aliases=[tgt,srv]],port,verify[aliases=[common_name,cn,hostname]]"
        # fmt: on
    )
    p.add_argument(
        "--module-class-name",
        action="append",
        default=[],
        help="specify class name for ansible module in format: module_name:class_name. e.g. unbound_dot:DnsOverTls",
    )
    p.add_argument(
        "--module-options-file",
        metavar="FILE",
        help="File containing module options in JSON format.",
    )

    g = p.add_argument_group("Operation options", "Options to control the operation of the script")
    g.add_argument("--list-models", action="store_true", help="List models in the plugin")
    g.add_argument("--list-apis", action="store_true", help="List APIs in the plugin")
    g.add_argument("--list-ansible-modules", action="store_true", help="List ansible modules to be created")
    g.add_argument("--generate", action="store_true", default=True, help="Generate ansible modules")
    g.add_argument("--no-generate", action="store_false", dest="generate", help="Disable module generation")

    return p

class Options(Base):
    def __init__(self):
        super().__init__()
        # store parsed module-arguments and module-class-name options
        self._module_arguments = {}
        self._module_class_names = {}
        self.modules = ['*']
        self.modules_exclude = []

        args = create_argument_parser().parse_args()
        self._args = args
        self.debug(f"Options: {args}")

        if args.verbose:
            logger.setLevel(logging.CRITICAL - args.verbose * 10)
        self.debug(f"Verbosity: {logger.getEffectiveLevel()}")

        for op in ["list_models", "list_apis", "list_ansible_modules", "generate"]:
            if getattr(args, op):
                self._operation = op
                break
        self.debug(f"Operation: {self._operation}")

        if args.module_options_file:
            self.debug(f"Loading module options from file: {args.module_options_file}")
            with open(args.module_options_file, "r", encoding="utf-8") as f:
                if args.module_options_file.endswith(".json"):
                    data  = json.load(f)
                elif args.module_options_file.rsplit(".", 1)[1] in ("yml", "yaml"):
                    data = yaml.safe_load(f)
            if "modules" in data:
                self.modules = data["modules"]
            if "modules_exclude" in data:
                self.modules_exclude = data["modules_exclude"]
            if "module_arguments" in data:
                self._module_arguments = data["module_arguments"]
            if "module_class_name" in data:
                self._module_class_names = data["module_class_name"]
        # override module options from command line
        if args.modules is not None:
            self.modules = args.modules.split(",")
        if args.modules_exclude is not None:
            self.modules_exclude = args.modules_exclude.split(",")
        if args.module_arguments:
            self._module_arguments.update(process_module_arguments_options(args.module_arguments))
        if args.module_class_name:
            self._module_class_names.update(self.process_module_class_name_options(args.module_class_name))

    def __getattr__(self, name):
        if hasattr(self._args, name):
            return getattr(self._args, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def operation(self):
        """Returns the operation to be performed."""
        return self._operation

    def find_module_arguments_spec(self, module_name):
        return self._module_arguments.get(module_name, None)

    def find_module_class_name(self, module_name):
        return self._module_class_names.get(module_name)

def process_module_class_name_options(options):
    result = {}
    for value in options:
        module, class_name = value.split(":", 1)
        result[module] = class_name
    return result

def process_module_arguments_options(options):
    result = {}
    for value in options:
        module, spec = process_module_arguments_option(value)
        result[module] = spec
    return result

def process_module_arguments_option(value):
    module, args = value.split(":", 1)
    pos = len(module) + 1
    result = {}
    context = [{}]
    for token in re.findall(r"[a-zA-Z0-9_]+|=\[|[\]\[=,]", args):
        ok = True
        token_desc = ""
        if token == ",":
            if isinstance(context[-1], list):
                # name[prop=[value1,<value2,...],...],...
                #                  ^      ^
                token_desc = "separator between list type property values"
            elif isinstance(context[-1], dict):
                # name[prop1=val1,prop2=val2,...],name[props],...
                #                ^          ^    ^
                token_desc = "end of a property or field"
            elif isinstance(context[-1], str):
                # field1[props],field2,field3,...
                #                     ^      ^
                token_desc = "end of field"
                key = context.pop()
                context[-1][key] = {}
            else:
                ok = False
        elif token == "[":
            # name[props]
            #     ^
            token_desc = "begining of field properties"
            if isinstance(context[-1], str):
                context.append({})
            else:
                ok = False
        elif token == "=":
            # name[prop=value1,prop2=value2,...]]
            #          ^            ^
            token_desc = "begining of property value (non-list)"
            # do nothing here
        elif token == "=[":
            # name[prop=[value1,value2,...]]
            #          ^^
            token_desc = "begining of list propery value"
            if isinstance(context[-1], str):
                context.append([])
            else:
                ok = False
        elif token == "]":
            if isinstance(context[-1], list):
                # name[prop=[value1,value2,...]],...
                #                             ^
                token_desc = "end of list type property"
            elif isinstance(context[-1], dict):
                # name1[props],name2[prop=[value1,value2,...]],...
                #            ^                               ^
                token_desc = "end of field property"
            else:
                ok = False
            val = context.pop()
            key = context.pop()
            context[-1][key] = val
        else:  # name or value
            if isinstance(context[-1], dict):
                token_desc = "field or property name"
                context.append(token)
            elif isinstance(context[-1], list):
                token_desc = "list property value"
                context[-1].append(token)
            elif isinstance(context[-1], str):
                token_desc = "property value"
                name = context.pop()
                context[-1][name] = token
            else:
                ok = False
        underline = "^" * len(token)
        if not ok:
            msg = f"Parse error: unexpected token found at {pos}: '{token}':\n"
            msg += f"    {value}\n{underline.rjust(pos + 4)}\n"
            raise ValueError(msg)
        debug(value)
        pos += len(token)
        width_after_token = len(value) - pos
        if width_after_token > len(token_desc) + 1:
            debug(underline.rjust(pos) + (" " + token_desc).ljust(width_after_token))
        else:
            debug((token_desc + " " + underline).rjust(pos) + " " * width_after_token)
    if context and isinstance(context[-1], str):
        # field with empty properties
        key = context.pop()
        context[-1][key] = {}
    context.pop()
    if context:
        raise ValueError("Syntax error: unexpected end of module arguments spec")
    debug("Parsed module arguments spec:", result)
    return module, result
