from plugins.plugin_base import BasePlugin

class HelloWorldPlugin(BasePlugin):
    def __init__(self):
        super().__init__("HelloWorld", "A simple plugin that returns 'Hello, World!'")

    def execute(self, *args, **kwargs):
        return "Hello, World!"