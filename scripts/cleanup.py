"""
Cleanup Utility Script — CyberTrace AI
Cleans temporary uploads, logs, and generated reports.
"""
import shutil
from pathlib import Path


def cleanup():
    print("🧹 Cleaning temporary directories...")
    dirs_to_clean = ["backend/uploads", "backend/logs", "reports/generated"]
    for d in dirs_to_clean:
        p = Path(d)
        if p.exists():
            for item in p.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"Cleaned {d}")
    print("✅ Cleanup complete!")


if __name__ == "__main__":
    cleanup()
