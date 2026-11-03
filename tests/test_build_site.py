import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "build_site", Path(__file__).resolve().parents[1] / "scripts/build_site.py")
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "explainers").mkdir()

    def page(self, name="20261103-example.html", title="Example", updated="2026-11-03"):
        path = self.root / "explainers" / name
        path.write_text(f'''<!doctype html><html><head><title>{title}</title>
<meta name="description" content="A &amp; B">
<meta name="explainer:created" content="2026-11-03">
<meta name="explainer:updated" content="{updated}"></head>
<body><button onclick="this.textContent='changed'">Try</button></body></html>''')
        return path

    def test_empty_gallery_and_only_publishable_files(self):
        (self.root / "secret.txt").write_text("not public")
        site.build(self.root, "commit-1")
        self.assertIn("まだありません", (self.root / "_site/index.html").read_text())
        self.assertFalse((self.root / "_site/secret.txt").exists())
        self.assertEqual(json.loads((self.root / "_site/build.json").read_text())["revision"], "commit-1")

    def test_order_escape_and_byte_preservation(self):
        old = self.page(title="&lt;script&gt; &amp; 日本語")
        new = self.page("20261103-new.html", updated="2026-11-04")
        entries = site.build(self.root)
        self.assertEqual([e["file"] for e in entries], [new.name, old.name])
        index = (self.root / "_site/index.html").read_text()
        self.assertIn("&lt;script&gt; &amp; 日本語", index)
        self.assertIn('href="explainers/20261103-new.html"', index)
        self.assertEqual(old.read_bytes(), (self.root / "_site/explainers" / old.name).read_bytes())

    def test_invalid_metadata_preserves_previous_build(self):
        page = self.page()
        site.build(self.root)
        before = (self.root / "_site/index.html").read_bytes()
        page.write_text(page.read_text().replace("2026-11-03", "2026-02-30"))
        with self.assertRaises(ValueError):
            site.build(self.root)
        self.assertEqual(before, (self.root / "_site/index.html").read_bytes())

    def test_update_keeps_same_url(self):
        page = self.page()
        first = site.build(self.root)[0]
        page.write_text(page.read_text().replace("Example", "Updated"))
        second = site.build(self.root)[0]
        self.assertEqual(first["file"], second["file"])
        self.assertNotEqual(first["sha256"], second["sha256"])

    def test_symlink_is_rejected(self):
        page = self.page()
        (self.root / "explainers/20261103-link.html").symlink_to(page)
        with self.assertRaises(ValueError):
            site.build(self.root)


if __name__ == "__main__":
    unittest.main()
