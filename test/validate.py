#!/usr/bin/env python3
"""Validate the distributable skill and synchronized release metadata."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()


def scalar(frontmatter, key):
    lines = frontmatter.splitlines()
    marker = key + ":"
    start = next((i for i, line in enumerate(lines) if line.strip().startswith(marker)), None)
    if start is None:
        raise AssertionError("missing frontmatter field: " + key)
    indent = len(lines[start]) - len(lines[start].lstrip())
    value = lines[start].strip()[len(marker):].strip()
    if value not in (">", ">-", "|", "|-"):
        return value.strip('"')
    parts = []
    for line in lines[start + 1:]:
        line_indent = len(line) - len(line.lstrip())
        if line.strip() and line_indent <= indent:
            break
        parts.append(line.strip())
    return " ".join(parts) if value.startswith(">") else "\n".join(parts)


def main():
    skill_path = ROOT / "SKILL.md"
    package_path = ROOT / "package.json"
    changelog_path = ROOT / "CHANGELOG.md"
    for required in (skill_path, package_path, changelog_path, ROOT / "LICENSE",
                     ROOT / "bin/building-design.js", ROOT / ".github/workflows/validate.yml",
                     ROOT / ".github/workflows/release.yml"):
        assert required.is_file(), "missing " + str(required.relative_to(ROOT))

    text = skill_path.read_text()
    assert text.startswith("---\n") and "\n---\n" in text, "invalid SKILL.md frontmatter"
    frontmatter, body = text.split("---", 2)[1:]
    name = scalar(frontmatter, "name")
    description = scalar(frontmatter, "description")
    compatibility = scalar(frontmatter, "compatibility")
    version = scalar(frontmatter, "version")
    assert name == ROOT.name and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
    assert description.startswith("Use when") and 1 <= len(description) <= 1024
    assert "дизайн" in description.lower()
    assert 1 <= len(compatibility) <= 500
    assert len(body.splitlines()) < 500
    assert scalar(frontmatter, "type") == "prompt"
    assert scalar(frontmatter, "whenToUse")
    assert not re.search(r"^  keywords:\s*$", frontmatter, re.MULTILINE), "metadata values must be strings"

    package = json.loads(package_path.read_text())
    assert package["name"] == name, "package.json and skill names differ"
    assert package["version"] == version, "package.json and SKILL.md versions differ"
    assert package["bin"] == {name: "bin/building-design.js"}
    assert package["license"] == scalar(frontmatter, "license")
    assert package["scripts"]["test"]
    assert re.search(r"^## \[" + re.escape(version) + r"\]", changelog_path.read_text(), re.MULTILINE), \
        "top-level release notes do not match package version"

    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
        if "://" not in link and not link.startswith("#"):
            target = link.split("#", 1)[0]
            assert not target.startswith("../"), "resource link escapes skill: " + link
            assert (ROOT / target).exists(), "broken resource link: " + link

    skill_files = [p for p in ROOT.rglob("SKILL.md") if ".git" not in p.parts]
    assert skill_files == [skill_path], "stray SKILL.md files: " + str(skill_files)
    print("PASS: building-design " + version + " distribution metadata and resources")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, StopIteration, ValueError) as error:
        print("FAIL:", error, file=sys.stderr)
        sys.exit(1)
