import os
import shutil

def clean_temp_files(directory="."): 
    """Cleans up temporary files in the specified directory."""
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                print(f"Removed: {os.path.join(root, d)}")
        for f in files:
            if f.endswith(".pyc") or f.endswith(".tmp"):
                os.remove(os.path.join(root, f))
                print(f"Removed: {os.path.join(root, f)}")

if __name__ == "__main__":
    print("Running development tools...")
    clean_temp_files()
    print("Development tools finished.")