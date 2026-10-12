# Arca documentation

The Arca documentation is built with mdBook and published to the `gh-pages` branch using the same build and publishing tools as `incentra-docs`. Both `main` and `deploy` can publish directly, so no branch sync workflow or personal access token is needed.

## Edit and preview

Documentation lives in `src/`. Edit `src/SUMMARY.md` to change the navigation and keep screenshots in `src/assets/`.

Install the same mdBook version used by CI:

```sh
cargo install mdbook --version 0.5.0-beta.1 --locked
mdbook serve --open
```

To build without starting a server, run `mdbook build`. Generated files go into `book/` and are ignored by Git. Mermaid diagrams load a pinned version of Mermaid from jsDelivr and require an internet connection.

## Publish to GitHub Pages

1. Push the source and workflow to `main` or `deploy`. Pull requests targeting these branches build the site for validation; pushes publish it.
2. After the first successful workflow creates `gh-pages`, open repository **Settings → Pages**. Choose **Deploy from a branch**, select **gh-pages** and **/ (root)**, then save.
3. Subsequent pushes to `main` or `deploy` rebuild and publish automatically. You can also run the workflow manually with either branch selected.

The default site URL is `https://brevis-network.github.io/arca-docs/`. The repository must have a GitHub plan that supports Pages for private repositories.

For a custom domain, add a root-level `CNAME` containing the domain, change `site-url` in `book.toml` to `/`, and configure the domain and DNS in GitHub Pages settings. CI copies `CNAME` into the published site when it exists.
