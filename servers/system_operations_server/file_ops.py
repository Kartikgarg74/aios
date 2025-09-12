# file_ops.py

import os

class FileOperations:
    def __init__(self):
        pass

    def read_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> bool:
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def delete_file(self, file_path: str) -> bool:
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False