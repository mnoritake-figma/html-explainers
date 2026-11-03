"""Build a static gallery from self-contained explainers; Python standard library only."""

import hashlib
import html
import json
import os
import re
import shutil
import tempfile
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.title = []
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        elif self.in_head and tag == "title":
            self.in_title = True
        elif self.in_head and tag == "meta":
            attrs = dict(attrs)
            key = attrs.get("name", "").lower()
            if key in {"description", "explainer:created", "explainer:updated"}:
                if key in self.meta:
                    raise ValueError(f"Duplicate metadata: {key}")
                self.meta[key] = attrs.get("content", "").strip()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "head":
            self.in_head = self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def read_entry(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Not a regular HTML file: {path.name}")
    if not re.fullmatch(r"\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*\.html", path.name):
        raise ValueError(f"Expected YYYYMMDD-kebab-case.html: {path.name}")
    data = path.read_bytes()
    parser = Metadata()
    parser.feed(data.decode("utf-8"))
    title = "".join(parser.title).strip()
    values = parser.meta
    if not title or any(not values.get(key) for key in
                        ("description", "explainer:created", "explainer:updated")):
        raise ValueError(f"Missing title or required metadata: {path.name}")
    created = values["explainer:created"]
    updated = values["explainer:updated"]
    for value in (created, updated):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError(f"Expected ISO date in {path.name}: {value}")
        date.fromisoformat(value)
    if created > updated or created.replace("-", "") != path.name[:8]:
        raise ValueError(f"Inconsistent creation/update dates: {path.name}")
    return {"file": path.name, "title": title, "description": values["description"],
            "created": created, "updated": updated,
            "sha256": hashlib.sha256(data).hexdigest()}


def render_index(entries):
    cards = []
    for entry in entries:
        e = {key: html.escape(value, quote=True) for key, value in entry.items()}
        cards.append(f'''<li><article>
<p class="date">更新 <time datetime="{e['updated']}">{e['updated']}</time></p>
<h2><a href="explainers/{e['file']}">{e['title']}</a></h2>
<p>{e['description']}</p>
<p class="date">作成 <time datetime="{e['created']}">{e['created']}</time></p>
</article></li>''')
    listing = ('<ul class="gallery">' + "\n".join(cards) + "</ul>" if entries else
               '<p class="empty">説明資料はまだありません。公開した資料がここに並びます。</p>')
    return '''<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="図や操作で理解を深めるHTML説明資料の一覧。">
<title>HTML Explainers</title>
<style>
:root{color:#000;background:#fff;font-family:"Noto Sans JP",sans-serif;line-height:1.8}
*{box-sizing:border-box}body{margin:0}main{max-width:1120px;margin:auto;padding:64px 28px}
header{border-bottom:2px solid #00a4af;padding-bottom:32px;margin-bottom:40px}
h1{font-size:clamp(2rem,6vw,3.5rem);line-height:1.2;margin:0 0 20px;letter-spacing:-.03em}
h2{font-size:1.25rem;line-height:1.5;margin:8px 0 16px;overflow-wrap:anywhere}
p{margin:0 0 12px}a{color:#000;text-decoration-color:#00a4af;text-underline-offset:5px}
a:hover{color:#00a4af}a:focus-visible{outline:3px solid #00a4af;outline-offset:5px}
.gallery{list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px;align-items:stretch}
.gallery li{display:flex;min-width:0}article{width:100%;border:1px solid #00a4af;border-radius:10px;padding:24px}
.date{font-size:.85rem}.empty{padding:32px 0}footer{margin-top:56px;border-top:1px solid #00a4af;padding-top:20px;font-size:.9rem}
@media(max-width:700px){main{padding:36px 20px}.gallery{grid-template-columns:1fr}}
</style></head><body><main>
<header><h1>HTML Explainers</h1><p>図や操作で、仕組みをひとつずつ理解する。</p>
<p>公開された説明資料を、更新日の新しい順に掲載しています。</p></header>
''' + listing + '''
<footer><a href="https://github.com/mnoritake-figma/html-explainers">GitHub リポジトリ</a></footer>
</main></body></html>
'''


def build(root, revision="local"):
    root = Path(root).resolve()
    source = root / "explainers"
    output = root / "_site"
    if source.is_symlink() or output.is_symlink():
        raise ValueError("Source/output directories must not be symbolic links")
    paths = sorted(source.glob("*.html"))
    entries = [read_entry(path) for path in paths]
    entries.sort(key=lambda e: (e["updated"], e["created"], e["file"]), reverse=True)
    # Validate every entry before touching an existing successful build.
    with tempfile.TemporaryDirectory(prefix=".site-build-", dir=root) as temp:
        stage = Path(temp) / "site"
        (stage / "explainers").mkdir(parents=True)
        for path in paths:
            shutil.copyfile(path, stage / "explainers" / path.name)
        (stage / "index.html").write_text(render_index(entries), encoding="utf-8")
        (stage / ".nojekyll").touch()
        (stage / "build.json").write_text(json.dumps(
            {"revision": revision, "entries": entries}, ensure_ascii=False, indent=2
        ) + "\n", encoding="utf-8")
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    return entries


if __name__ == "__main__":
    entries = build(Path(__file__).resolve().parents[1], os.environ.get("GITHUB_SHA", "local"))
    print(f"Built {len(entries)} explainers into _site/")
