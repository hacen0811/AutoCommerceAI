import sys
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = BASE_DIR / "browser_profile" / "source_sites"


def chrome_path():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for path in candidates:
        if Path(path).exists():
            return path

    return "chrome"


def open_source_url(url):
    if not url:
        print("[AutoCommerceAI] URL이 비어 있습니다.")
        return False

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.Popen(
        [
            chrome_path(),
            f"--user-data-dir={PROFILE_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
            url,
        ],
        shell=False,
    )

    print("[AutoCommerceAI] URL 열기:", url)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[AutoCommerceAI] URL이 필요합니다.")
        sys.exit(1)

    open_source_url(sys.argv[1])