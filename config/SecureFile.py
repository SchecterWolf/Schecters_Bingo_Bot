__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import os
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pathlib import Path

class SecureFile:
    __SIZE_SALT = 16
    __SIZE_IV = 12

    def __init__(self, fileName: str):
        self.secureFile = Path(fileName)

    def getData(self) -> str:
        if not self.secureFile.exists():
            return ""

        # Read in encrypted file
        with self.secureFile.open("rb") as file:
            fileData = file.read()

        salt = fileData[:SecureFile.__SIZE_SALT]
        iv = fileData[SecureFile.__SIZE_SALT:SecureFile.__SIZE_SALT + SecureFile.__SIZE_IV]
        tag = fileData[28:44]
        data = fileData[44:]

        key = self._getKey(salt)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()

        return str(decryptor.update(data) + decryptor.finalize())

    def saveFile(self, inFile: str) -> bool:
        inputFile = Path(inFile)
        if not inputFile.exists():
            return False

        salt = os.urandom(SecureFile.__SIZE_SALT)
        iv = os.urandom(SecureFile.__SIZE_IV)

        key = self._getKey(salt)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        with inputFile.open("rb") as file:
            fileData = file.read()

        encryptedData = encryptor.update(fileData) + encryptor.finalize()

        with self.secureFile.open("wb") as file:
            file.write(salt + iv + encryptor.tag + encryptedData)

        return True

    def _getKey(self, salt: bytes) -> bytes:
        # Get the password from the command line
        print(f"Enter password for file \"{self.secureFile.name}\": ")
        password: bytearray = bytearray(sys.stdin.buffer.readline())

        # Derive the decrypting key
        ret = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            ).derive(password)

        # Clear out password
        for i in range(len(password)):
            password[i] = ord('0')
        sys.stdin.flush()

        return ret

