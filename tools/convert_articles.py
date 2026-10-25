#!/usr/bin/env python3
"""
One-off helper: converts your hand-written article pages into Markdown files
for the new CMS setup.

Run it from the repo root BEFORE you replace index.html with the new one,
because it also reads the old front page (for summaries, lead/side slots, etc.).

    python3 tools/convert_articles.py

Reads : index.html (old)  and  articles/*.html (old)
Writes: _articles/<name>.md   (one per article)

It never deletes or changes your old files. Check the output, then remove the
old articles/*.html (Jekyll will regenerate those URLs from the .md files).
"""
import html
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_articles"


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def strip_tags(text):
    return clean(re.sub(r"<[^>]+>", "", text or ""))


def first(pattern, text, flags=re.S):
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


def fix_path(src):
    """../images/x.jpg or images/x.jpg -> /images/x.jpg"""
    if not src:
        return None
    src = src.strip()
    src = re.sub(r"^(\.\./|\./)+", "", src)
    return src if src.startswith("/") else "/" + src


class ToMarkdown(HTMLParser):
    """Tiny HTML -> Markdown converter for article bodies."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.buf = []
        self.hrefs = []
        self.prefix = ""
        self.quote = None  # list of paragraphs while inside <blockquote>
        self.list_kind = []
        self.li_n = 0

    def flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        return text

    def emit(self, text):
        if not text:
            return
        if self.quote is not None:
            self.quote.append(text)
        else:
            self.blocks.append(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("p", "h2", "h3", "h4"):
            self.emit(self.flush())
            self.prefix = {"h2": "## ", "h3": "### ", "h4": "#### "}.get(tag, "")
        elif tag == "a":
            self.hrefs.append(a.get("href", ""))
            self.buf.append("[")
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("*")
        elif tag == "br":
            self.buf.append("  \n")
        elif tag == "blockquote":
            self.emit(self.flush())
            self.quote = []
        elif tag == "cite":
            self.emit(self.flush())
        elif tag in ("ul", "ol"):
            self.emit(self.flush())
            self.list_kind.append(tag)
            self.li_n = 0
        elif tag == "li":
            self.emit(self.flush())
            self.li_n += 1

    def handle_endtag(self, tag):
        if tag in ("p", "h2", "h3", "h4"):
            text = self.flush()
            if text:
                self.emit(self.prefix + text)
            self.prefix = ""
        elif tag == "a":
            href = self.hrefs.pop() if self.hrefs else ""
            self.buf.append(f"]({href})")
        elif tag in ("strong", "b"):
            self.buf.append("**")
        elif tag in ("em", "i"):
            self.buf.append("*")
        elif tag == "cite":
            text = self.flush()
            if text:
                self.emit(f"<cite>{text}</cite>")
        elif tag == "blockquote":
            self.emit(self.flush())
            parts, self.quote = self.quote, None
            lines = []
            for i, part in enumerate(parts):
                if i:
                    lines.append(">")
                lines.append("> " + part)
            if lines:
                self.blocks.append("\n".join(lines))
        elif tag == "li":
            text = self.flush()
            kind = self.list_kind[-1] if self.list_kind else "ul"
            marker = f"{self.li_n}." if kind == "ol" else "-"
            if text:
                # consecutive list items are joined into one block later
                self.blocks.append(("LI", f"{marker} {text}"))
        elif tag in ("ul", "ol"):
            if self.list_kind:
                self.list_kind.pop()

    def handle_data(self, data):
        self.buf.append(data)

    def markdown(self):
        self.emit(self.flush())
        out, items = [], []
        for b in self.blocks:
            if isinstance(b, tuple):
                items.append(b[1])
                continue
            if items:
                out.append("\n".join(items))
                items = []
            out.append(b)
        if items:
            out.append("\n".join(items))
        return "\n\n".join(out)


def parse_index(path):
    """Pull summary / lead-side slot / crop flag for each story on the old front page."""
    info = {}
    if not path.exists():
        print(f"! {path} not found: summaries and front-page slots will be blank")
        return info
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"<article\b([^>]*)>(.*?)</article>", text, re.S):
        attrs, block = m.group(1), m.group(2)
        slug = first(r'href="(?:\.?/)?articles/([^"/]+?)\.html"', block)
        if not slug:
            continue
        d = {}
        if "lead-story" in attrs:
            d["front_page"] = "lead"
        elif "front-page-side-story" in attrs:
            d["front_page"] = "side"
        summary = first(r'<p class="story-summary">(.*?)</p>', block) \
            or first(r"<p>(.*?)</p>", block)
        d["summary"] = strip_tags(summary) if summary else None
        cat = first(r'<(?:span class="category"|p class="story-category")>(.*?)</', block)
        if cat:
            cat = strip_tags(cat)
            if "Exclusive" in cat:
                d["exclusive"] = True
                cat = re.sub(r"\s*[·•|-]\s*Exclusive", "", cat).strip()
            d["section"] = cat
        d["image_fit"] = "fit-image" in block
        d["image"] = fix_path(first(r'<img[^>]*\bsrc="([^"]+)"', block))
        d["image_alt"] = clean(first(r'<img[^>]*\balt="([^"]*)"', block) or "")
        meta = first(r'<(?:span class="byline"|p class="story-meta")>(.*?)</', block)
        if meta:
            parts = [p.strip() for p in strip_tags(meta).split("·")]
            d["author"] = re.sub(r"^By\s+", "", parts[0])
            if len(parts) > 1:
                d["date_text"] = parts[1]
        info[slug] = d
    return info


def parse_date(text):
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass
    return None


def q(value):
    """Quote a string for YAML (JSON strings are valid YAML)."""
    return json.dumps(value, ensure_ascii=False)


def convert(path, idx):
    slug = path.stem
    src = path.read_text(encoding="utf-8")
    fm = dict(idx.get(slug, {}))
    warnings = []

    title = first(r'<h1 class="article-title">(.*?)</h1>', src)
    fm["title"] = strip_tags(title) if title else None
    section = first(r'<header class="article-header">\s*<span class="category">(.*?)</span>', src)
    if section:
        fm["section"] = strip_tags(section)
    standfirst = first(r'<p class="standfirst">(.*?)</p>', src)
    fm["standfirst"] = strip_tags(standfirst) if standfirst else None

    byline = first(r'<div class="byline">(.*?)</div>', src) or ""
    for span in re.findall(r"<span>(.*?)</span>", byline, re.S):
        s = strip_tags(span)
        if s.lower().startswith("by "):
            fm["author"] = s[3:].strip()
        elif re.search(r"min read", s, re.I):
            fm["read_time"] = s
        elif parse_date(s):
            fm["date_text"] = s

    hero = re.search(r'<div class="hero-image">\s*<img[^>]*?src="([^"]+)"[^>]*?alt="([^"]*)"', src, re.S)
    if hero:
        fm["image"] = fix_path(hero.group(1))
        fm["image_alt"] = clean(hero.group(2))
    cap = first(r'<figcaption class="image-caption">(.*?)</figcaption>', src)
    fm["image_caption"] = strip_tags(cap) if cap else None

    body_html = first(r'<div class="article-body">(.*?)<div class="article-end">', src)
    if body_html is None:
        body_html = first(r'<div class="article-body">(.*?)</div>\s*</article>', src) or ""
        warnings.append("couldn't find the end-of-article marker; check the end of the body")
    conv = ToMarkdown()
    conv.feed(body_html)
    body = conv.markdown()

    fm["date"] = parse_date(fm.get("date_text", ""))
    for needed in ("title", "section", "date", "author", "image", "summary"):
        if not fm.get(needed):
            warnings.append(f"missing {needed}: fill it in by hand")

    lines = ["---"]
    lines.append(f"title: {q(fm.get('title') or slug)}")
    lines.append(f"section: {q(fm.get('section') or '')}")
    if fm.get("exclusive"):
        lines.append("exclusive: true")
    lines.append(f"front_page: {fm.get('front_page', 'none')}")
    lines.append(f"date: {fm.get('date') or ''}")
    lines.append(f"author: {q(fm.get('author') or '')}")
    if fm.get("read_time"):
        lines.append(f"read_time: {q(fm['read_time'])}")
    lines.append(f"image: {q(fm.get('image') or '')}")
    lines.append(f"image_alt: {q(fm.get('image_alt') or '')}")
    if fm.get("image_caption"):
        lines.append(f"image_caption: {q(fm['image_caption'])}")
    if fm.get("image_fit"):
        lines.append("image_fit: true")
    lines.append(f"summary: {q(fm.get('summary') or '')}")
    if fm.get("standfirst"):
        lines.append(f"standfirst: {q(fm['standfirst'])}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    lines.append("")

    OUT.mkdir(exist_ok=True)
    (OUT / f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")
    return slug, warnings


def main():
    articles = sorted((ROOT / "articles").glob("*.html"))
    if not articles:
        sys.exit("No articles/*.html found. Run this from the repo root.")
    index = ROOT / "index.html"
    if index.exists() and "{% " in index.read_text(encoding="utf-8"):
        sys.exit("index.html is already the NEW template. Restore the old one first "
                 "(git checkout index.html) and run again.")
    idx = parse_index(index)
    for path in articles:
        slug, warnings = convert(path, idx)
        print(f"OK  _articles/{slug}.md")
        for w in warnings:
            print(f"    ! {w}")
    print("\nDone. Check the files in _articles/, then see the setup steps.")


if __name__ == "__main__":
    main()
