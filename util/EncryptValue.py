#!/usr/bin/env python3
__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2025 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

from config.SecureFile import SecureFile

def main():
    inFile = input("Enter file to encrypt: ")
    outFile = f"{inFile}.enc"
    sec = SecureFile(outFile)

    if not sec.saveFile(inFile):
        print(f"Failed to encrypt \"{inFile}\"")

    print("Successfully created encrypted file \"{outFile}\"")
    print("Make sure the keep the .enc extension when configuring the file,")
    print("so the bot knows to try and decrypt it. Files without the extension")
    print("will be treated as clear text files.")

if __name__ == '__main__':
    main()
