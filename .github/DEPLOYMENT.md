# Arca documentation publishing

`main` stores the original GitBook pages at the repository root, including `README.md`, `SUMMARY.md`, and `.gitbook/assets/`. GitBook continues syncing to this branch. Keep GitBook syntax and source paths here.

On each push to `main`, the sync workflow converts a separate copy, tests it, and validates its mdBook build. It writes that copy to the generated `deploy` branch, then explicitly calls the publishing workflow with the exact converted commit. The publishing workflow checks out that commit, builds the website, and writes it to `gh-pages`.

The explicit workflow call is required because pushes made with `GITHUB_TOKEN` do not trigger another push workflow. No personal access token is needed. Pull requests to `main` test conversion and build the site without updating either publication branch.

## Edit and preview

Edit the GitBook pages on `main`. Change `SUMMARY.md` for navigation. Publishing settings live in `.github/mdbook/`; the converter lives in `.github/scripts/process_markdown.py`. Do not edit generated files in `deploy` or `gh-pages`, because the next sync replaces them.

Install mdBook and the Python validation tools:

```sh
cargo install mdbook --version 0.5.0-beta.1 --locked
python3 -m pip install pytest==9.0.3 ruff==0.14.0
```

To preview, stage new pages and assets so the converter includes them, then run:

```sh
python3 .github/scripts/process_markdown.py --output .mdbook
mdbook serve .mdbook --open
```

The output directory must be new. For repeated previews, choose another output directory or remove the previous generated `.mdbook/` first. Conversion never edits the original GitBook pages. Unknown GitBook directives fail conversion so unsupported content cannot disappear silently. Fenced code blocks and Mermaid source are preserved.

Mermaid diagrams use a pinned CDN dependency and require an internet connection. Run `pytest -q` and `ruff check` before committing changes to the converter.

## Publishing and recovery

Push to `main` or manually run **Sync GitBook main to mdBook deploy** with `main` selected. To rebuild an existing converted version, run **Deploy mdBook site to GitHub Pages** with `source-ref` set to `deploy` or a converted commit SHA. Pushing directly to `deploy` also builds and publishes that branch.

GitHub Pages serves **gh-pages / (root)**. The custom domain is `docs.arca.market`, configured in `.github/mdbook/CNAME`, with `site-url = "/"` in `.github/mdbook/book.toml`. The repository must have a GitHub plan supporting Pages for private repositories.
