from krita import *
from .banana_docker import BananaDocker


class KritaBananaExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        pass


# Register Extension
Krita.instance().addExtension(KritaBananaExtension(Krita.instance()))
# Register Docker
Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(
        "krita_banana_docker", DockWidgetFactoryBase.DockRight, BananaDocker
    )
)
