from pathlib import Path
from fnmatch import fnmatch
from . import Base, log, log_v
from .options import Options
from .ansible import ModuleSpec, ModuleTemplates
from .opnsense import Plugin


class Generator(Base):
    # In this class, model refers to the model item in the plugin
    def __init__(self, options: Options = None):
        super().__init__()
        opts = options or Options()
        # self.options = options or Options()
        self._plugin = Plugin(
            name=opts.plugin_name,
            plugin_dir=opts.plugin_dir,
            models_dir=opts.models_dir,
            controllers_dir=opts.controllers_dir,
        )
        self._dest_dir = Path(opts.dest_dir)
        self._templates = ModuleTemplates()
        self._operation = opts.operation
        self._options = opts
        self._module_specs = []

    def load_models(self):
        self._plugin.load_models()

    def load_apis(self):
        self._plugin.load_apis()

    def count_model_items(self):
        return self._plugin.count_model_items()

    def count_models(self):
        return len(self._plugin.models)

    def count_apis(self):
        return self._plugin.count_apis()

    def count_controllers(self):
        return len(self._plugin.apis)

    def get_models(self):
        return self._plugin.get_model_items()

    def do_main(self):
        self.analyze()
        self.do_actions()

    def analyze(self):
        """Analyze plugin for ansible modules generation."""
        log("===> Analyzing plugin: %s", self._plugin.name)

        self.load_models()
        log_v("%d items are found in %d model file(s)", self.count_model_items(), self.count_models())
        self.load_apis()
        log_v("%d apis are found in %d api controller file(s)", self.count_apis(), self.count_controllers())
        for model in self.get_models():
            spec = ModuleSpec(model, self._plugin, self._options)
            self._module_specs.append(spec)

    def do_actions(self):
        getattr(self, self._operation, lambda: None)()

    def list_models(self):
        self._plugin.list_model_items()

    def list_apis(self):
        self._plugin.list_apis()

    def list_ansible_modules(self):
        for module in self._module_specs:
            print(
                module.module_name
                + "\n  model: "
                + module.model.get_reference()
                + "\n  fields: "
                + ", ".join(module.fields.keys())
            )

    def generate(self):
        specs = [s for s in self._module_specs if self.is_target(s)]
        if not specs:
            log("No modules found to generate.")
            return
        for spec in specs:
            log(f"Generating module {spec.module_name}...")
            self.generate_files(spec)

    def is_target(self, spec: ModuleSpec):
        for include_pattern in self._options.modules:
            if fnmatch(spec.module_name, include_pattern):
                for exclude_pattern in self._options.modules_exclude:
                    if fnmatch(spec.module_name, exclude_pattern):
                        return False
                return True

    def generate_files(self, module: ModuleSpec):
        self.generate_module_file(module)
        self.generate_module_utils_main_file(module)

    def generate_module_file(self, spec):
        t = self._templates.get_module_template()
        output = t.render(
            module_name=spec.module_name,
            class_name=spec.class_name,
            module_args=spec.get_module_arguments(),
        )
        destfile = Path(self._dest_dir).joinpath("modules", spec.module_name + ".py")
        destfile.parent.mkdir(exist_ok=True, parents=True)
        destfile.write_text(output, encoding="UTF-8")
        log(f"  {destfile}")

    def generate_module_utils_main_file(self, spec: ModuleSpec):
        t = self._templates.get_module_utils_main_template()
        # list_fields = []
        # for name, field in module.fields.items():
        #     if isinstance(field, AsListType):
        #         print(f"{name} is an AsListType")
        #         if name == "networks":
        #             print(f"{name} is list: {field.as_list}")
        #             list_fields.append(name)
        # field.model = module
        res_apis = spec.get_resource_apis()
        res_api = list(res_apis.values())[0]
        rel_api = spec.get_reload_api()
        api = dict(
            KEY_PATH=spec.api_key_path,
            MOD=res_api["module"],
            CONT=res_api["controller"],
        )
        if rel_api is not None:
            if res_api["controller"] != rel_api["controller"]:
                api["CONT_REL"] = rel_api["controller"]
            api["CMD_REL"] = rel_api["command"]
        output = t.render(
            class_name=spec.class_name,
            API=api,
            CMDS={cmd: api["command"] for cmd, api in res_apis.items()},
            EXIST_ATTR=spec.model_name,
            FIELDS=spec.fields_data,
            IMPORTS=spec.get_custom_imports(),
        )
        destfile = Path(self._dest_dir).joinpath("module_utils", "main", spec.module_name + ".py")
        destfile.parent.mkdir(exist_ok=True, parents=True)
        destfile.write_text(output, encoding="UTF-8")
        log(f"  {destfile}")
