import os
import shutil
from datetime import datetime

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = script_dir
backup_dir = os.path.join(db_dir, "backups")
os.makedirs(backup_dir, exist_ok=True)

def backup_db_files():
    for filename in os.listdir(db_dir):
        if filename.endswith(".db"):
            src = os.path.join(db_dir, filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
            shutil.copy2(src, dst)
            print(f"Backed up {filename} to {dst}")

if __name__ == "__main__":
    backup_db_files() 