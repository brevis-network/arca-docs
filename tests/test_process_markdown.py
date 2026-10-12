"""Regression checks for the GitBook to mdBook publishing boundary."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".github/scripts/process_markdown.py"
SPEC = importlib.util.spec_from_file_location("process_markdown", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)


def test_gitbook_page_keeps_content_images_and_heading_anchors():
    source = '''---
description: A GitBook page
---
{% stepper %}
{% step %}
### Connect GitHub

<figure><img src="../.gitbook/assets/screen shot.png"><figcaption>Profile</figcaption></figure>
{% endstep %}
{% endstepper %}
'''
    result = converter.process_markdown(source)
    assert result.startswith("\n\n### Connect GitHub")
    assert "../assets/screen shot.png" in result
    assert "<figcaption>Profile</figcaption>" in result
    assert "{%" not in result
    assert "description:" not in result


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_fenced_code_and_mermaid_are_preserved(fence):
    source = f'{fence}text\n{{% unknown %}}\n.gitbook/assets/example.png\n{fence}\n'
    source += '```mermaid\nflowchart TD\n    A --> B\n```\n'
    assert converter.process_markdown(source) == source


def test_frontmatter_removal_does_not_consume_thematic_breaks():
    source = '# Overview\n\n---\n\nKeep this paragraph.\n\n---\n'
    assert converter.process_markdown(source) == source


def test_summary_parts_and_raw_html_local_links():
    source = '''# Table of contents
## Welcome
* [Overview](README.md)
<a href="nested/README.md#intro">Overview</a>
<a href='guide.md#connect-github'>Guide</a>
<a href="https://example.com/README.md">External</a>
'''
    result = converter.process_markdown(source, summary=True)
    assert "# Welcome\n" in result
    assert "[Overview](README.md)" in result
    assert 'href="nested/index.html#intro"' in result
    assert "href='guide.html#connect-github'" in result
    assert 'href="https://example.com/README.md"' in result


def test_unsupported_directive_fails_instead_of_silently_dropping_content():
    with pytest.raises(ValueError, match="Unsupported GitBook directive"):
        converter.process_markdown("{% unknown %}\nContent\n")


def test_embeds_and_tabs():
    source = '''{% tabs %}
{% tab title="macOS" %}
{% embed url="https://example.com/video" %}
Install the app.
{% endtab %}
{% endtabs %}
'''
    result = converter.process_markdown(source)
    assert "### macOS" in result
    assert "[View content](<https://example.com/video>)" in result
    assert "Install the app." in result
    assert "{%" not in result


def test_conversion_copies_only_tracked_source_and_never_modifies_main(tmp_path):
    files = {
        "README.md": "# Overview\n{% stepper %}\n{% endstepper %}\n",
        "SUMMARY.md": "# Summary\n* [Overview](README.md)\n",
        ".gitbook/assets/image.png": "image bytes",
        ".github/mdbook/book.toml": '[book]\ntitle = "Arca"\n',
        ".github/mdbook/theme/custom.css": "figure img { max-width: 100%; }",
        ".github/mdbook/CNAME": "docs.arca.market\n",
        ".github/workflows/gh-pages.yml": "name: Publish\n",
        ".github/DEPLOYMENT.md": "Maintainer instructions",
        "tests/test_example.py": "assert True",
        ".gitignore": ".mdbook/\n",
    }
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    (tmp_path / "private-untracked.md").write_text("Do not publish scratch files")
    output = tmp_path / ".mdbook"
    converter.prepare_book(tmp_path, output)
    for name, content in files.items():
        assert (tmp_path / name).read_text() == content
    assert (output / "src/assets/image.png").read_text() == "image bytes"
    assert "{%" not in (output / "src/README.md").read_text()
    assert (output / "CNAME").read_text() == "docs.arca.market\n"
    assert (output / ".github/workflows/gh-pages.yml").is_file()
    assert not (output / "src/.github").exists()
    assert not (output / "src/tests").exists()
    assert not (output / "src/private-untracked.md").exists()
    with pytest.raises(FileExistsError):
        converter.prepare_book(tmp_path, output)
