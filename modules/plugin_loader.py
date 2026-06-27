import importlib
import pkgutil
from pathlib import Path

def discover_plugins():
    plugins = []
    try:
        import plugins as plugin_pkg
    except Exception:
        return plugins

    package_path = Path(plugin_pkg.__file__).parent

    for module_info in pkgutil.iter_modules([str(package_path)]):
        name = module_info.name
        try:
            module = importlib.import_module(f"plugins.{name}")
            plugin_cls = getattr(module, "Plugin", None)
            if plugin_cls is None:
                continue
            plugins.append(plugin_cls())
        except Exception as e:
            plugins.append(BrokenPlugin(name, str(e)))

    return plugins

class BrokenPlugin:
    id = "broken"
    name = "Fehlerhaftes Plugin"
    category = "Fehler"
    engine = "Unbekannt"
    icon = "⚠"
    description = "Dieses Plugin konnte nicht geladen werden."
    available = False
    kind = "broken"

    def __init__(self, plugin_name, error):
        self.id = f"broken_{plugin_name}"
        self.name = f"Fehler: {plugin_name}"
        self.error = error

    def status(self):
        return "Fehler"

    def details(self):
        return f"Plugin konnte nicht geladen werden:\n\n{self.error}"
