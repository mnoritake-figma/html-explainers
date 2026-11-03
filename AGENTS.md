# HTML Explainers

This public repository publishes self-contained HTML explainers at
https://mnoritake-figma.github.io/html-explainers/.

- Add pages in `explainers/YYYYMMDD-kebab-case.html`. Keep an existing filename
  when updating a page so its public URL remains stable.
- Each page needs a nonempty `<title>` and these head metadata fields:
  `description`, `explainer:created`, and `explainer:updated`.
  Dates use `YYYY-MM-DD`; creation date must match the filename date and updates
  must be on or after creation. Use the user's local date.
- Keep CSS, JavaScript, and SVG inline so the page works locally without network
  access. Only flat `explainers/*.html` files are included in the published site.
- Run `python3 -m unittest discover -s tests -v` and
  `python3 scripts/build_site.py` before publishing. Preview the affected page
  and gallery; check important interactions and narrow screens.
- `_site/` is generated. Do not hand-edit it or commit it. The builder generates
  the gallery and a `build.json` containing the source revision and page hashes.
- Commit only files belonging to the request. Never use force push to resolve
  concurrent additions. Fetch the latest head and reapply only your own changes.
- A push to `main` publishes automatically through `.github/workflows/pages.yml`.
  PRs run the build and tests without deploying. If direct updates are blocked,
  open a PR and report that publication is waiting for merge.
- Report publication as complete only after deployment succeeds and the public
  page matches the intended content; `build.json` supports revision/hash checks.
