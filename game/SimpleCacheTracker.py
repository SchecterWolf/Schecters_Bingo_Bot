__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

class SimpleCacheTracker:
    def __init__(self):
        self.__dirty: bool = True

    def getIsDirty(self) -> bool:
        return self.__dirty

    def setClean(self):
        self.__dirty = False

    def __setattr__(self, name, value):
        hasAttr = hasattr(self, name)
        changedAttr = name != "_SimpleCacheTracker__dirty" and getattr(self, name) != value if hasAttr else True

        super().__setattr__(name, value)

        if changedAttr:
            self.__dirty = True

