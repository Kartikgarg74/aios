import os
import importlib.util
from typing import List, Dict, Any, Optional
import logging
from plugins.plugin_base import BasePlugin

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages dynamic loading, unloading, and execution of plugins."""

    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.loaded_plugins: Dict[str, Any] = {}
        self._ensure_plugin_dir_exists()

    def _ensure_plugin_dir_exists(self):
        """Ensures the plugin directory exists."""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            logger.info(f"Created plugin directory: {self.plugin_dir}")

    def load_plugin(self, plugin_name: str) -> Optional[Any]:
        """Loads a plugin dynamically."""
        if plugin_name in self.loaded_plugins:
            logger.info(f"Plugin '{plugin_name}' already loaded.")
            return self.loaded_plugins[plugin_name]

        plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        if not os.path.exists(plugin_path):
            logger.error(f"Plugin file not found: {plugin_path}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Assuming the plugin class name is the camel-cased version of the file name
                class_name = ''.join(word.capitalize() for word in plugin_name.split('_'))
                if hasattr(module, class_name) and issubclass(getattr(module, class_name), BasePlugin):
                    self.loaded_plugins[plugin_name] = getattr(module, class_name)()
                    logger.info(f"Plugin '{plugin_name}' loaded successfully.")
                    return self.loaded_plugins[plugin_name]
                else:
                    logger.error(f"Plugin class '{class_name}' not found in module '{plugin_name}'.")
                    return None
            else:
                logger.error(f"Could not create module spec for plugin '{plugin_name}'.")
                return None
        except Exception as e:
            logger.error(f"Error loading plugin '{plugin_name}': {e}")
            return None

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unloads a plugin."""
        if plugin_name not in self.loaded_plugins:
            logger.info(f"Plugin '{plugin_name}' is not loaded.")
            return False

        try:
            del self.loaded_plugins[plugin_name]
            # Optionally, remove from sys.modules if truly needed, but be cautious
            # if plugin might be referenced elsewhere.
            if plugin_name in list(sys.modules.keys()): # Use list() to avoid RuntimeError during iteration
                del sys.modules[plugin_name]
            logger.info(f"Plugin '{plugin_name}' unloaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_name}': {e}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Returns a loaded plugin by name."""
        return self.loaded_plugins.get(plugin_name)

    def list_plugins(self) -> List[str]:
        """Lists all available plugin files in the plugin directory."""
        try:
            return [f.replace('.py', '') for f in os.listdir(self.plugin_dir) if f.endswith('.py') and f != '__init__.py' and f != 'plugin_manager.py' and f != 'plugin_base.py']
        except FileNotFoundError:
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return []

    def reload_plugin(self, plugin_name: str) -> Optional[Any]:
        """Reloads an already loaded plugin."""
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin '{plugin_name}' is not loaded, attempting to load it instead of reload.")
            return self.load_plugin(plugin_name)
        
        plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        if not os.path.exists(plugin_path):
            logger.error(f"Plugin file not found for reloading: {plugin_path}")
            return None

        try:
            # Unload first to ensure a clean reload
            if self.unload_plugin(plugin_name):
                return self.load_plugin(plugin_name)
            else:
                logger.error(f"Failed to unload plugin '{plugin_name}' for reloading.")
                return None
        except Exception as e:
            logger.error(f"Error reloading plugin '{plugin_name}': {e}")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example Usage:
    # Create a dummy plugin file for testing
    dummy_plugin_content = """
# dummy_plugin.py
def greet(name):
    return f"Hello, {name}! This is from dummy_plugin."

class MyPlugin:
    def __init__(self):
        self.name = "MyDummyPlugin"

    def get_info(self):
        return f"Info from {self.name}"
"""
    
    plugin_test_dir = "./test_plugins"
    os.makedirs(plugin_test_dir, exist_ok=True)
    with open(os.path.join(plugin_test_dir, "dummy_plugin.py"), "w") as f:
        f.write(dummy_plugin_content)

    manager = PluginManager(plugin_test_dir)

    # List available plugins
    print(f"Available plugins: {manager.list_plugins()}")

    # Load a plugin
    dummy_plugin = manager.load_plugin("dummy_plugin")
    if dummy_plugin:
        print(dummy_plugin.greet("World"))
        my_plugin_instance = dummy_plugin.MyPlugin()
        print(my_plugin_instance.get_info())

    # Try to load again (should show already loaded message)
    manager.load_plugin("dummy_plugin")

    # Unload a plugin
    manager.unload_plugin("dummy_plugin")

    # Try to use unloaded plugin (should fail)
    try:
        dummy_plugin.greet("Test")
    except NameError as e:
        print(f"Expected error after unloading: {e}")

    # Reload a plugin
    reloaded_plugin = manager.reload_plugin("dummy_plugin")
    if reloaded_plugin:
        print(reloaded_plugin.greet("Reloaded World"))

    # Clean up dummy plugin file and directory
    os.remove(os.path.join(plugin_test_dir, "dummy_plugin.py"))
    os.rmdir(plugin_test_dir)