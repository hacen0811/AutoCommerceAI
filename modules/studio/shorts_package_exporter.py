import json
from datetime import datetime
from pathlib import Path
import re

from config.settings import EXPORTS_DIR


class ShortsPackageExporter:
    def __init__(self):
        self.out_dir = EXPORTS_DIR / "shorts_packages"
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def save(self, package):
        project = package.get("project", {})
        product = package.get("product", {})
        name = product.get("name") or project.get("name") or "shorts_package"
        safe = self.safe_name(name)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.out_dir / f"{safe}_{stamp}"

        json_path = base.with_suffix(".json")
        txt_path = base.with_suffix(".txt")
        md_path = base.with_suffix(".md")

        json_path.write_text(json.dumps(package, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        txt_path.write_text(self.to_text(package), encoding="utf-8")
        md_path.write_text(self.to_markdown(package), encoding="utf-8")

        return {
            "json": str(json_path),
            "txt": str(txt_path),
            "md": str(md_path),
            "folder": str(self.out_dir),
        }

    def safe_name(self, text):
        text = re.sub(r"[^\w가-힣\s-]", "", str(text))
        text = re.sub(r"\s+", "_", text).strip("_")
        return text[:48] or "shorts_package"

    def to_text(self, package):
        product = package.get("product", {})
        lines = []
        lines.append("[쇼핑쇼츠 제작 패키지]")
        lines.append("")
        lines.append(f"상품명: {product.get('name')}")
        lines.append(f"댓글 키워드: {product.get('keyword')}")
        lines.append(f"타오바오: {product.get('taobao_keyword')}")
        lines.append(f"도우인: {product.get('douyin_keyword')}")
        lines.append("")
        lines.append("[15초 대본]")
        for item in package.get("scripts", {}).get("15s", []):
            lines.append(f"{item.get('time')} / {item.get('role')} : {item.get('line')}")
        lines.append("")
        lines.append("[25초 대본]")
        for item in package.get("scripts", {}).get("25s", []):
            lines.append(f"{item.get('time')} / {item.get('role')} : {item.get('line')}")
        lines.append("")
        lines.append("[CapCut 편집안]")
        for item in package.get("capcut", {}).get("timeline", []):
            lines.append(f"{item.get('time')} : {item.get('edit')}")
        lines.append("")
        lines.append("[유튜브 쇼츠]")
        yt = package.get("youtube", {})
        lines.append(f"제목: {yt.get('title')}")
        lines.append(f"설명:\n{yt.get('description')}")
        lines.append(f"해시태그: {yt.get('hashtags')}")
        lines.append("")
        lines.append("[인스타 릴스]")
        ig = package.get("instagram", {})
        lines.append(f"본문:\n{ig.get('caption')}")
        lines.append(f"해시태그: {ig.get('hashtags')}")
        return "\n".join(lines)

    def to_markdown(self, package):
        product = package.get("product", {})
        lines = [
            "# 쇼핑쇼츠 제작 패키지",
            "",
            f"## 상품",
            f"- 상품명: {product.get('name')}",
            f"- 댓글 키워드: {product.get('keyword')}",
            f"- 타오바오: `{product.get('taobao_keyword')}`",
            f"- 도우인: `{product.get('douyin_keyword')}`",
            "",
            "## 타오바오 TOP10",
        ]
        for item in product.get("taobao_top10", []):
            lines.append(f"{item.get('rank')}. `{item.get('query')}` - {item.get('purpose')} / {item.get('score')}")

        lines += ["", "## 도우인 TOP10"]
        for item in product.get("douyin_top10", []):
            lines.append(f"{item.get('rank')}. `{item.get('query')}` - {item.get('purpose')} / {item.get('score')}")

        lines += ["", "## 15초 대본"]
        for item in package.get("scripts", {}).get("15s", []):
            lines.append(f"- **{item.get('time')} / {item.get('role')}**: {item.get('line')}")

        lines += ["", "## 25초 대본"]
        for item in package.get("scripts", {}).get("25s", []):
            lines.append(f"- **{item.get('time')} / {item.get('role')}**: {item.get('line')}")

        lines += ["", "## CapCut 편집안"]
        for item in package.get("capcut", {}).get("timeline", []):
            lines.append(f"- **{item.get('time')}**: {item.get('edit')}")

        lines += ["", "## 썸네일"]
        thumb = package.get("thumbnail", {})
        lines.append(f"- 메인 문구: {thumb.get('main_text')}")
        lines.append(f"- 보조 문구: {thumb.get('sub_text')}")
        lines.append(f"- 구성: {thumb.get('composition')}")

        lines += ["", "## 유튜브 쇼츠"]
        yt = package.get("youtube", {})
        lines.append(f"- 제목: {yt.get('title')}")
        lines.append(f"- 설명:\n\n{yt.get('description')}")
        lines.append(f"- 해시태그: {yt.get('hashtags')}")

        lines += ["", "## 인스타 릴스"]
        ig = package.get("instagram", {})
        lines.append(f"- 본문:\n\n{ig.get('caption')}")
        lines.append(f"- 해시태그: {ig.get('hashtags')}")
        return "\n".join(lines)
