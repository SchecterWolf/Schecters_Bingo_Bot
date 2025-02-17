__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from typing import Any

class Result:
    def __init__(self, result, response="", additionalType: Any = None):
        self.result = result
        self.responseMsg = response
        self.additional = additionalType

