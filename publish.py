#!/usr/bin/env python3
"""Turn markdown notes in the Obsidian vault into the site's content.

Jack writes notes. This reads them. Nothing else about the site needs an
editor, a build tool, or a line of HTML.

  vault/Site/Blog/*.md      -> landing/blog/posts.json      (the blog)
  vault/Site/Projects/*.md  -> showcase/projects.json       (showcase cards)
  vault/Site/Media/*        -> landing/media/ + showcase/media/

A note is a normal Obsidian note: frontmatter at the top, markdown under it.
Anything it does not understand it leaves alone rather than failing, because
the person writing the notes is not going to be here to read a traceback.

Run it by hand:   python3 publish.py
Or leave the timer to do it every two minutes.
"""

import html
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

VAULT = Path(os.environ.get("SITE_VAULT", "/data/vault/Site"))
LANDING = Path(os.environ.get("SITE_LANDING", str(Path.home() / "landing")))
SHOWCASE = Path(os.environ.get("SITE_SHOWCASE", str(Path.home() / "fleet" / "showcase")))

MEDIA_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif",
             ".mp4", ".webm", ".mov", ".m4v"}
VIDEO_EXT = {".mp4", ".webm", ".mov", ".m4v"}


# ── frontmatter ──────────────────────────────────────────────────────────────
def split_front(text):
    """Return (dict, body). Frontmatter is optional; a note without it still
    publishes, it just has to get its title from the first heading."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end]
            text = text[end + 4:].lstrip("\n")
            for line in block.splitlines():
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k, v = k.strip().lower(), v.strip()
                if v.startswith("[") and v.endswith("]"):
                    v = [p.strip().strip("\"'") for p in v[1:-1].split(",") if p.strip()]
                else:
                    v = v.strip("\"'")
                meta[k] = v
    return meta, text


# ── markdown, the parts a person actually types ──────────────────────────────
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    # an image or a video, written the same way in both cases
    def media(m):
        alt, src = m.group(1), m.group(2)
        if Path(src).suffix.lower() in VIDEO_EXT:
            return (f'<video src="{src}" controls muted loop playsinline '
                    f'preload="metadata"></video>')
        return f'<img src="{src}" alt="{alt}" loading="lazy">'
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", media, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", s)
    return s


def markdown(text):
    out, lines, i = [], text.replace("\r\n", "\n").split("\n"), 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):                      # fenced code
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i])); i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        if not stripped:
            i += 1; continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):  # rule
            out.append("<hr>"); i += 1; continue

        m = re.match(r"(#{1,6})\s+(.*)", stripped)           # heading
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv}>{inline(m.group(2))}</h{lv}>"); i += 1; continue

        if stripped.startswith(">"):                         # quote
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue

        if re.match(r"[-*+]\s+", stripped):                  # bullets
            buf = []
            while i < len(lines) and re.match(r"[-*+]\s+", lines[i].strip()):
                buf.append(inline(re.sub(r"^[-*+]\s+", "", lines[i].strip()))); i += 1
            out.append("<ul>" + "".join(f"<li>{b}</li>" for b in buf) + "</ul>")
            continue

        if re.match(r"\d+[.)]\s+", stripped):                # numbers
            buf = []
            while i < len(lines) and re.match(r"\d+[.)]\s+", lines[i].strip()):
                buf.append(inline(re.sub(r"^\d+[.)]\s+", "", lines[i].strip()))); i += 1
            out.append("<ol>" + "".join(f"<li>{b}</li>" for b in buf) + "</ol>")
            continue

        buf = []                                             # paragraph
        while i < len(lines) and lines[i].strip() and not re.match(
                r"(#{1,6}\s|>|[-*+]\s|\d+[.)]\s|```)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        para = inline(" ".join(buf))
        # an image on its own line is a figure, not a run of text
        tag = "figure" if re.fullmatch(r"\s*<(img|video)[^>]*>\s*", para) else "p"
        out.append(f"<{tag}>{para}</{tag}>")
    return "\n".join(out)


def plain(text, limit=200):
    """First paragraph, stripped to words — used as the card excerpt."""
    for block in text.split("\n\n"):
        b = block.strip()
        if not b or b.startswith(("#", ">", "-", "!", "```")):
            continue
        b = re.sub(r"[*`\[\]]|\(https?://[^)]+\)", "", b).strip()
        return (b[: limit - 1] + "…") if len(b) > limit else b
    return ""


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-") or "post"


# ── reading the folders ──────────────────────────────────────────────────────
def read_notes(folder):
    items = []
    if not folder.is_dir():
        return items
    for f in sorted(folder.glob("*.md")):
        if f.name.startswith((".", "_")) or f.name.upper().startswith("HOW TO"):
            continue
        try:
            raw = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  ! skipped {f.name}: {e}", file=sys.stderr); continue
        meta, body = split_front(raw)
        if str(meta.get("draft", "")).lower() in ("true", "yes", "1"):
            continue
        title = meta.get("title") or next(
            (l.lstrip("# ").strip() for l in body.splitlines()
             if l.strip().startswith("#")), f.stem)
        item = dict(meta)
        item["title"] = title
        item["slug"] = meta.get("slug") or slugify(f.stem)
        item["html"] = markdown(body)
        item["excerpt"] = meta.get("excerpt") or plain(body)
        item["file"] = f.name
        tags = item.get("tags", [])
        item["tags"] = ([t.strip() for t in tags.split(",") if t.strip()]
                        if isinstance(tags, str) else list(tags))
        # "runs on = 2x P100 | lines = 559" — readable in Obsidian, a readout
        # row on the card. Written with pipes so a comma in a value is safe.
        stats = item.get("stats")
        if isinstance(stats, str):
            item["stats"] = [[k.strip(), v.strip()] for k, v in
                             (pair.split("=", 1) for pair in stats.split("|")
                              if "=" in pair)]
        elif not isinstance(stats, list):
            item["stats"] = []
        for flag in ("feature", "pinned"):
            if flag in item:
                item[flag] = str(item[flag]).lower() in ("true", "yes", "1")
        items.append(item)
    return items


def copy_media(dests):
    src = VAULT / "Media"
    n = 0
    if not src.is_dir():
        return 0
    for f in src.iterdir():
        if not f.is_file() or f.suffix.lower() not in MEDIA_EXT:
            continue
        for d in dests:
            d.mkdir(parents=True, exist_ok=True)
            out = d / f.name
            if not out.exists() or out.stat().st_mtime < f.stat().st_mtime:
                shutil.copy2(f, out); n += 1
    return n


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)          # swap in whole, so a reader never sees half a file


def main():
    if not VAULT.is_dir():
        print(f"no {VAULT} — nothing to publish"); return 0

    posts = read_notes(VAULT / "Blog")
    posts.sort(key=lambda p: str(p.get("date", "")), reverse=True)
    write_json(LANDING / "blog" / "posts.json",
               {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "posts": posts})

    projects = read_notes(VAULT / "Projects")
    # features lead, then newest first — the two big cards should be the two
    # things worth leading with, not whichever happened to be edited last
    projects.sort(key=lambda p: (bool(p.get("feature")), str(p.get("date", ""))),
                  reverse=True)
    write_json(SHOWCASE / "projects.json",
               {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "projects": projects})

    files = copy_media([LANDING / "media", SHOWCASE / "media"])
    print(f"published {len(posts)} posts, {len(projects)} projects, {files} media files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
