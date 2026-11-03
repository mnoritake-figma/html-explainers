# html-explainers
learnings

[Public gallery](https://mnoritake-figma.github.io/html-explainers/)

Self-contained HTML explainers live in `explainers/YYYYMMDD-kebab-case.html`.
Each page includes a title and the following metadata in its `<head>`:

```html
<title>Page title</title>
<meta name="description" content="A short summary of the explanation.">
<meta name="explainer:created" content="2026-11-03">
<meta name="explainer:updated" content="2026-11-03">
```

Use actual local dates. Keep the filename and creation date when revising a
page. Inline CSS, JavaScript, and SVG keep each explainer usable offline.

To check and preview (Python 3.9+, no packages required):

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
python3 -m http.server --directory _site
```

A push to `main` runs the tests, generates the gallery, and deploys `_site/`
through GitHub Actions. Pull requests only run validation. Do not commit the
generated `_site/` directory. Only `explainers/*.html` is copied into the site;
drafts and source material should remain outside this public repository.

Individual pages are available at
`https://mnoritake-figma.github.io/html-explainers/explainers/FILENAME.html`.
The generated `build.json` records the source revision and page SHA-256 hashes
for checking that a deployment contains the intended content.
