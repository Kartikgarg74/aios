import abc

class BasePlugin(abc.ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abc.abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError