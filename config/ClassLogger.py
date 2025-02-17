__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import threading

from .Log import Logger, LogLevel

class ClassLogger:
    def __init__(self, className):
        self.className = className
        self.logger = Logger()

    def log(self, level: LogLevel, msg: str):
        tid = threading.get_ident()
        msg_format = f"[{self.className}]({tid}) {msg}"
        self.logger.log(level, msg_format)

