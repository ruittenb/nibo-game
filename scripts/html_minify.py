#!/usr/bin/env python3
"""
html_minify.py - Minifies a single HTML file with embedded CSS.

Features:
- Shortens class names and ID names across both CSS and HTML
- Strips CSS and HTML comments
- Collapses whitespace in CSS and HTML
- Minifies inline style blocks

Usage:
    python html_minify.py input.html -o output.html
    python html_minify.py input.html                    # prints to stdout
"""

import re
import sys
import argparse
import string
from html.parser import HTMLParser
from io import StringIO


def generate_short_names():
    """Generate short CSS-valid class/ID names: a, b, ..., z, A, ..., Z, aa, ab, ..."""
    chars = string.ascii_letters  # a-z, A-Z
    n = 0
    while True:
        name = ""
        num = n
        name = chars[num % len(chars)]
        num //= len(chars)
        while num > 0:
            num -= 1
            name = chars[num % len(chars)] + name
            num //= len(chars)
        yield name
        n += 1


def extract_style_blocks(html):
    """Extract all <style>...</style> blocks and their positions."""
    pattern = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.DOTALL | re.IGNORECASE)
    blocks = []
    for m in pattern.finditer(html):
        blocks.append({
            'start': m.start(),
            'end': m.end(),
            'open_tag': m.group(1),
            'css': m.group(2),
            'close_tag': m.group(3),
        })
    return blocks


def find_css_classes_and_ids(css):
    """Find all class and ID selectors in CSS."""
    # First, strip comments and strings to avoid false matches
    cleaned = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    cleaned = re.sub(r'"[^"]*"', '""', cleaned)
    cleaned = re.sub(r"'[^']*'", "''", cleaned)

    classes = set()
    ids = set()

    # Match class selectors: .name
    # Exclude decimal numbers like 1.5em by requiring non-digit before the dot
    for m in re.finditer(r'(?<![0-9])\.(-?[a-zA-Z_][\w-]*)', cleaned):
        classes.add(m.group(1))

    # Match ID selectors: #name
    # Exclude hex colors: #xxx, #xxxxxx, #xxxx, #xxxxxxxx (3,4,6,8 hex digits)
    for m in re.finditer(r'#(-?[a-zA-Z_][\w-]*)', cleaned):
        name = m.group(1)
        # Skip if it looks like a hex color (all hex chars, length 3/4/6/8)
        if re.match(r'^[0-9a-fA-F]{3,8}$', name) and len(name) in (3, 4, 6, 8):
            continue
        ids.add(name)
    return classes, ids


def find_html_classes_and_ids(html):
    """Find all class and id attribute values in HTML."""
    classes = set()
    ids = set()
    # class="foo bar baz"
    for m in re.finditer(r'class\s*=\s*["\']([^"\']*)["\']', html, re.IGNORECASE):
        for c in m.group(1).split():
            classes.add(c)
    # id="foo"
    for m in re.finditer(r'id\s*=\s*["\']([^"\']*)["\']', html, re.IGNORECASE):
        ids.add(m.group(1).strip())
    return classes, ids


def minify_css(css):
    """Basic CSS minification: remove comments, collapse whitespace."""
    # Remove comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    # Remove whitespace around special characters
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{}:;,>~+])\s*', r'\1', css)
    # Remove trailing semicolons before }
    css = re.sub(r';}', '}', css)
    # Remove leading/trailing whitespace
    css = css.strip()
    return css


def minify_html(html):
    """Basic HTML minification: remove comments, collapse whitespace."""
    # Remove HTML comments (but not conditional comments)
    html = re.sub(r'<!--(?!\[).*?-->', '', html, flags=re.DOTALL)
    # Collapse whitespace between tags
    html = re.sub(r'>\s+<', '><', html)
    # Collapse runs of whitespace to single space
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def rename_in_css(css, class_map, id_map):
    """Replace class and ID names in CSS with short versions."""
    # Sort by length descending to avoid partial replacements
    for old, new in sorted(class_map.items(), key=lambda x: -len(x[0])):
        # Replace .classname ensuring it's a complete selector token
        css = re.sub(
            r'\.' + re.escape(old) + r'(?=[\s{:.,>~+\[\]#)!]|$)',
            '.' + new, css
        )
    for old, new in sorted(id_map.items(), key=lambda x: -len(x[0])):
        css = re.sub(
            r'#' + re.escape(old) + r'(?=[\s{:.,>~+\[\]#)!]|$)',
            '#' + new, css
        )
    return css


def rename_in_html(html, class_map, id_map):
    """Replace class and ID attribute values in HTML."""
    def replace_class_attr(m):
        prefix = m.group(1)  # class="  or class='
        quote = m.group(2)
        value = m.group(3)
        classes = value.split()
        renamed = ' '.join(class_map.get(c, c) for c in classes)
        return prefix + renamed + quote

    # Handle class="..." and class='...'
    html = re.sub(
        r'(class\s*=\s*(["\']))([^"\']*)\2',
        replace_class_attr,
        html,
        flags=re.IGNORECASE
    )

    def replace_id_attr(m):
        prefix = m.group(1)
        quote = m.group(2)
        value = m.group(3).strip()
        renamed = id_map.get(value, value)
        return prefix + renamed + quote

    # Handle id="..." and id='...'
    html = re.sub(
        r'(id\s*=\s*(["\']))([^"\']*)\2',
        replace_id_attr,
        html,
        flags=re.IGNORECASE
    )

    # Also handle href="#id" and similar anchor references
    def replace_href_hash(m):
        prefix = m.group(1)
        quote = m.group(2)
        id_val = m.group(3)
        renamed = id_map.get(id_val, id_val)
        return prefix + renamed + quote

    html = re.sub(
        r'(href\s*=\s*(["\'])#)([^"\']*)\2',
        replace_href_hash,
        html,
        flags=re.IGNORECASE
    )

    return html


def process(html_content):
    """Main processing pipeline."""
    # 1. Extract style blocks
    style_blocks = extract_style_blocks(html_content)

    # 2. Collect all CSS content
    all_css = '\n'.join(b['css'] for b in style_blocks)

    # 3. Find all class/ID names in CSS and HTML
    css_classes, css_ids = find_css_classes_and_ids(all_css)
    html_classes, html_ids = find_html_classes_and_ids(html_content)

    # Only rename names that appear in BOTH CSS and HTML (safe intersection)
    # Plus names that appear in CSS (they might be used dynamically, but
    # for a single static file, CSS-only names are safe to rename too)
    all_classes = css_classes | html_classes
    all_ids = css_ids | html_ids

    # 4. Build renaming maps
    name_gen = generate_short_names()
    # Reserve names that might conflict with CSS keywords
    reserved = {'a', 'b', 'i', 's', 'p', 'q', 'u'}  # common HTML tags

    class_map = {}
    id_map = {}

    # Sort for deterministic output
    for cls in sorted(all_classes):
        short = next(name_gen)
        while short in reserved:
            short = next(name_gen)
        # Only rename if it actually saves characters
        if len(short) < len(cls):
            class_map[cls] = short

    for id_name in sorted(all_ids):
        short = next(name_gen)
        while short in reserved:
            short = next(name_gen)
        if len(short) < len(id_name):
            id_map[id_name] = short

    # 5. Process: rename in CSS blocks, then minify CSS
    result = html_content
    # Work backwards so positions stay valid
    for block in reversed(style_blocks):
        css = block['css']
        css = rename_in_css(css, class_map, id_map)
        css = minify_css(css)
        replacement = block['open_tag'] + css + block['close_tag']
        result = result[:block['start']] + replacement + result[block['end']:]

    # 6. Rename in HTML (outside of style blocks)
    result = rename_in_html(result, class_map, id_map)

    # 7. Minify HTML
    result = minify_html(result)

    return result, class_map, id_map


def main():
    parser = argparse.ArgumentParser(description='Minify HTML with class/ID renaming')
    parser.add_argument('input', help='Input HTML file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-m', '--map', action='store_true',
                        help='Print the renaming map to stderr')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        html_content = f.read()

    result, class_map, id_map = process(html_content)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        orig_size = len(html_content.encode('utf-8'))
        new_size = len(result.encode('utf-8'))
        saving = (1 - new_size / orig_size) * 100 if orig_size else 0
        print(f"Original: {orig_size} bytes", file=sys.stderr)
        print(f"Minified: {new_size} bytes", file=sys.stderr)
        print(f"Saved:    {saving:.1f}%", file=sys.stderr)
    else:
        print(result)

    if args.map:
        if class_map:
            print("\nClass renaming:", file=sys.stderr)
            for old, new in sorted(class_map.items()):
                print(f"  .{old} -> .{new}", file=sys.stderr)
        if id_map:
            print("\nID renaming:", file=sys.stderr)
            for old, new in sorted(id_map.items()):
                print(f"  #{old} -> #{new}", file=sys.stderr)


if __name__ == '__main__':
    main()
