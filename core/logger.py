from pathlib import Path
from datetime import datetime


class AppLogger:
    def __init__(self, path="logs/app.log"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def info(self, message):
        self.write("INFO", message)

    def error(self, message):
        self.write("ERROR", message)

    def write(self, level, message):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.path.write_text(
            (self.path.read_text(encoding="utf-8") if self.path.exists() else "")
            + f"[{ts}] {level}: {message}\n",
            encoding="utf-8",
        )
