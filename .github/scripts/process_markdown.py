"""Prepare a separate mdBook checkout from tracked GitBook source files."""

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def convert_prose(content: str) -> str:
    """Convert GitBook directives and links outside fenced code blocks."""
    content = content.replace(".gitbook/assets/", "assets/")

    def convert_tag(match: re.Match[str]) -> str:
        tag = match.group(1).strip()
        name = tag.split()[0]
        if name in {
            "stepper", "step", "endstepper", "endstep", "code", "endcode",
            "endhint", "tabs", "endtabs", "endtab", "endcontent-ref",
        }:
            return ""
        if name == "hint":
            return "\n> **Note:**\n"
        if name == "tab":
            title = re.search(r'title=[\"\']([^\"\']+)[\"\']', tag)
            if title is None:
                raise ValueError(f"Missing tab title: {tag}")
            return f"\n### {title.group(1)}\n"
        if name in {"embed", "content-ref"}:
            url = re.search(r'url=[\"\']([^\"\']+)[\"\']', tag)
            if url is None:
                raise ValueError(f"Missing URL: {tag}")
            return f"\n[View content](<{url.group(1)}>)\n" if name == "embed" else ""
        raise ValueError(f"Unsupported GitBook directive: {tag}")

    content = re.sub(r"\{%\s*(.*?)\s*%\}", convert_tag, content, flags=re.DOTALL)

    def convert_html_link(match: re.Match[str]) -> str:
        url = urlsplit(match.group(2))
        if url.scheme or url.netloc or not url.path.endswith(".md"):
            return match.group(0)
        path = Path(url.path)
        filename = "index.html" if path.name == "README.md" else f"{path.stem}.html"
        target = urlunsplit(url._replace(path=str(path.with_name(filename))))
        return f"href={match.group(1)}{target}{match.group(1)}"

    return re.sub(r"href=([\"\'])(.*?)[\"\']", convert_html_link, content)


def process_markdown(content: str, *, summary: bool = False) -> str:
    content = re.sub(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", "", content, count=1, flags=re.DOTALL)
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    prose: list[str] = []
    fence: str | None = None
    for line in lines:
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence is None and marker:
            result.append(convert_prose("".join(prose)))
            prose = []
            fence = marker.group(1)
            result.append(line)
        elif fence is not None:
            result.append(line)
            if re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*", line):
                fence = None
        else:
            prose.append(line)
    result.append(convert_prose("".join(prose)))
    content = "".join(result)
    if summary:
        content = re.sub(r"^## ", "# ", content, flags=re.MULTILINE)
    return content


def prepare_book(repo_root: Path, output_dir: Path) -> None:
    """Copy source to a new directory; never rewrite the GitBook checkout."""
    if output_dir.exists():
        raise FileExistsError(f"Output directory must be new: {output_dir}")
    files = subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=repo_root,
    ).decode().split("\0")
    source = output_dir / "src"
    source.mkdir(parents=True)
    for filename in filter(None, files):
        path = Path(filename)
        if path.parts[0] in {".github", "tests"} or filename == ".gitignore":
            continue
        relative = Path(filename.replace(".gitbook/assets/", "assets/", 1))
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".md":
            content = (repo_root / path).read_text()
            destination.write_text(process_markdown(content, summary=path.name == "SUMMARY.md"))
        else:
            shutil.copy2(repo_root / path, destination)
    if not (source / "SUMMARY.md").is_file():
        raise FileNotFoundError("GitBook source must contain SUMMARY.md")
    config = repo_root / ".github" / "mdbook"
    shutil.copy2(config / "book.toml", output_dir / "book.toml")
    shutil.copytree(config / "theme", output_dir / "theme")
    if (config / "CNAME").is_file():
        shutil.copy2(config / "CNAME", output_dir / "CNAME")
    # A push made with GITHUB_TOKEN does not trigger this workflow. The main
    # sync workflow calls it explicitly; it also supports manual deploy pushes.
    workflows = output_dir / ".github" / "workflows"
    workflows.mkdir(parents=True)
    shutil.copy2(repo_root / ".github/workflows/gh-pages.yml", workflows / "gh-pages.yml")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(".mdbook"))
    args = parser.parse_args()
    prepare_book(Path(__file__).resolve().parents[2], args.output.resolve())
