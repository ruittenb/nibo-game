#!/usr/bin/env python3
"""
html_minify.py - Minifies a single HTML file with embedded CSS.

Features:
- Shortens class names and ID names across both CSS and HTML
- Updates all cross-references: for=, href=#, url(#), filter=url(#)
- Strips CSS and HTML comments
- Collapses whitespace in CSS and HTML
- Minifies inline style blocks
- Preserves CSS custom properties (--variable-names)

Usage:
    python html_minify.py input.html -o output.html
    python html_minify.py input.html                    # prints to stdout
    python html_minify.py input.html -o output.html -m  # also print renaming map
"""

import re
import sys
import argparse
import string


def generate_short_names():
    """Generate short CSS-valid class/ID names: a, b, ..., z, A, ..., Z, aa, ab, ..."""
    chars = string.ascii_letters
    n = 0
    while True:
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


def find_css_classes_ids_and_vars(css):
    """Find all class selectors, ID selectors, and CSS custom properties in CSS."""
    # Strip comments and strings to avoid false matches
    cleaned = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    cleaned = re.sub(r'"[^"]*"', '""', cleaned)
    cleaned = re.sub(r"'[^']*'", "''", cleaned)

    # Find CSS custom properties first (before removing them for class/id scan)
    css_vars = set()
    for m in re.finditer(r'(--[\w-]+)', cleaned):
        css_vars.add(m.group(1))

    # Remove CSS custom property names for class/id scanning
    cleaned_for_scan = re.sub(r'--[\w-]+', '', cleaned)

    classes = set()
    ids = set()

    for m in re.finditer(r'(?<![0-9])\.(-?[a-zA-Z_][\w-]*)', cleaned_for_scan):
        classes.add(m.group(1))

    for m in re.finditer(r'#(-?[a-zA-Z_][\w-]*)', cleaned_for_scan):
        name = m.group(1)
        if re.match(r'^[0-9a-fA-F]{3,8}$', name) and len(name) in (3, 4, 6, 8):
            continue
        ids.add(name)

    return classes, ids, css_vars


def find_html_classes_and_ids(html):
    """Find all class and id attribute values in HTML."""
    classes = set()
    ids = set()
    for m in re.finditer(r'class\s*=\s*["\']([^"\']*)["\']', html, re.IGNORECASE):
        for c in m.group(1).split():
            classes.add(c)
    for m in re.finditer(r'id\s*=\s*["\']([^"\']*)["\']', html, re.IGNORECASE):
        ids.add(m.group(1).strip())
    return classes, ids


def minify_css(css):
    """Basic CSS minification: remove comments, collapse whitespace.
    
    Preserves required spaces:
    - Around + and - (needed in calc() expressions)
    - Before : when preceded by a word char (descendant combinator before pseudo-selectors)
    """
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    css = re.sub(r'\s+', ' ', css)
    # Strip whitespace around structural characters, but NOT around : or +
    # because : could be a pseudo-selector after a descendant combinator,
    # and + is needed in calc()
    css = re.sub(r'\s*([{};,>~])\s*', r'\1', css)
    # Now handle : carefully — only strip space AFTER colon (property values),
    # not BEFORE colon (which could be a descendant combinator before pseudo-selector)
    css = re.sub(r':\s+', ':', css)
    css = re.sub(r';}', '}', css)
    css = css.strip()
    return css


def minify_html_whitespace(html):
    """Basic HTML minification: remove comments, collapse whitespace."""
    html = re.sub(r'<!--(?!\[).*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'>\s+<', '><', html)
    html = re.sub(r'\s+', ' ', html)
    return html.strip()


def rename_in_css(css, class_map, id_map, var_map):
    """Replace class selectors, ID selectors, and CSS variables in CSS."""
    # 1. Rename CSS custom properties (longest-first, word-boundary aware)
    for old, new in sorted(var_map.items(), key=lambda x: -len(x[0])):
        css = re.sub(re.escape(old) + r'(?![\w-])', new, css)

    # 2. Replace class selectors (longest-first to avoid partial matches)
    for old, new in sorted(class_map.items(), key=lambda x: -len(x[0])):
        css = re.sub(
            r'\.' + re.escape(old) + r'(?=[\s{:.,>~+\[\]#)!;]|$)',
            '.' + new, css
        )

    # 3. Replace ID selectors
    for old, new in sorted(id_map.items(), key=lambda x: -len(x[0])):
        css = re.sub(
            r'#' + re.escape(old) + r'(?=[\s{:.,>~+\[\]#)!;]|$)',
            '#' + new, css
        )

    # 4. Rename IDs inside url(#...) in CSS values
    for old, new in sorted(id_map.items(), key=lambda x: -len(x[0])):
        css = css.replace(f'url(#{old})', f'url(#{new})')

    # 5. Rename IDs inside CSS attribute selectors like [for="id-name"]
    def replace_attr_selector(m):
        attr = m.group(1)   # e.g. 'for'
        op = m.group(2)     # e.g. '=' or '~=' etc.
        quote = m.group(3)  # e.g. '"'
        value = m.group(4)  # e.g. 'level-0'
        renamed = id_map.get(value, value)
        return f'[{attr}{op}{quote}{renamed}{quote}]'

    css = re.sub(
        r'\[(\w+)([~|^$*]?=)(["\'])([^"\']*)\3\]',
        replace_attr_selector, css
    )

    return css


def rename_in_html(html, class_map, id_map, var_map):
    """Replace class, id, for, href=#, url(#), and CSS variable references in HTML."""

    # 1. class="..."
    def replace_class_attr(m):
        prefix = m.group(1)
        quote = m.group(2)
        value = m.group(3)
        classes = value.split()
        renamed = ' '.join(class_map.get(c, c) for c in classes)
        return prefix + renamed + quote

    html = re.sub(
        r'(class\s*=\s*(["\']))([^"\']*)\2',
        replace_class_attr, html, flags=re.IGNORECASE
    )

    # 2. id="..."
    def replace_id_attr(m):
        prefix = m.group(1)
        quote = m.group(2)
        value = m.group(3).strip()
        return prefix + id_map.get(value, value) + quote

    html = re.sub(
        r'(id\s*=\s*(["\']))([^"\']*)\2',
        replace_id_attr, html, flags=re.IGNORECASE
    )

    # 3. for="..." (labels referencing input IDs)
    def replace_for_attr(m):
        prefix = m.group(1)
        quote = m.group(2)
        value = m.group(3).strip()
        return prefix + id_map.get(value, value) + quote

    html = re.sub(
        r'(for\s*=\s*(["\']))([^"\']*)\2',
        replace_for_attr, html, flags=re.IGNORECASE
    )

    # 4. href="#id"
    def replace_href_hash(m):
        prefix = m.group(1)
        quote = m.group(2)
        id_val = m.group(3)
        return prefix + id_map.get(id_val, id_val) + quote

    html = re.sub(
        r'(href\s*=\s*(["\'])#)([^"\']*)\2',
        replace_href_hash, html, flags=re.IGNORECASE
    )

    # 5. url(#id) in any attribute
    for old, new in sorted(id_map.items(), key=lambda x: -len(x[0])):
        html = html.replace(f'url(#{old})', f'url(#{new})')

    # 6. CSS variables in inline style="" attributes
    for old, new in sorted(var_map.items(), key=lambda x: -len(x[0])):
        html = re.sub(re.escape(old) + r'(?![\w-])', new, html)

    return html


def process(html_content):
    """Main processing pipeline."""
    style_blocks = extract_style_blocks(html_content)
    all_css = '\n'.join(b['css'] for b in style_blocks)

    css_classes, css_ids, css_vars = find_css_classes_ids_and_vars(all_css)
    html_classes, html_ids = find_html_classes_and_ids(html_content)
    all_classes = css_classes | html_classes
    all_ids = css_ids | html_ids

    # Also find CSS vars used in inline style= attributes in HTML
    html_vars = set(re.findall(r'(--[\w-]+)', html_content))
    all_vars = css_vars | html_vars

    # Build renaming maps (separate generators per namespace — they can't collide)
    reserved = {'a', 'b', 'i', 's', 'p', 'q', 'u'}

    class_map = {}
    id_map = {}
    var_map = {}

    class_gen = generate_short_names()
    for cls in sorted(all_classes):
        short = next(class_gen)
        while short in reserved:
            short = next(class_gen)
        if len(short) < len(cls):
            class_map[cls] = short

    id_gen = generate_short_names()
    for id_name in sorted(all_ids):
        short = next(id_gen)
        while short in reserved:
            short = next(id_gen)
        if len(short) < len(id_name):
            id_map[id_name] = short

    var_gen = generate_short_names()
    for var_name in sorted(all_vars):
        short = next(var_gen)
        while short in reserved:
            short = next(var_gen)
        short_var = '--' + short
        if len(short_var) < len(var_name):
            var_map[var_name] = short_var

    # Process CSS blocks (rename + minify)
    result = html_content
    for block in reversed(style_blocks):
        css = block['css']
        css = rename_in_css(css, class_map, id_map, var_map)
        css = minify_css(css)
        replacement = block['open_tag'] + css + block['close_tag']
        result = result[:block['start']] + replacement + result[block['end']:]

    # Rename in HTML
    result = rename_in_html(result, class_map, id_map, var_map)

    # Minify HTML whitespace
    result = minify_html_whitespace(result)

    return result, class_map, id_map, var_map


def main():
    parser = argparse.ArgumentParser(description='Minify HTML with class/ID renaming')
    parser.add_argument('input', help='Input HTML file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-m', '--map', action='store_true',
                        help='Print the renaming map to stderr')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        html_content = f.read()

    result, class_map, id_map, var_map = process(html_content)

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
        if var_map:
            print("\nCSS variable renaming:", file=sys.stderr)
            for old, new in sorted(var_map.items()):
                print(f"  {old} -> {new}", file=sys.stderr)


if __name__ == '__main__':
    main()
