#!/usr/bin/env python3
"""
html_minify.py - Minifies a single HTML file with embedded CSS.

Features:
- Inlines constant CSS variables (eliminates var() + declaration overhead)
- Evaluates calc() expressions that become fully resolvable after inlining
- Resolves undefined var() references to their fallback values
- Shortens class names, ID names, and CSS variable names
- Renames <div> to <d> and <span> to <t>
- Shortens hex colors where possible (#aabbcc -> #abc)
- Strips units from zero values (0px -> 0)
- Removes unnecessary quotes from attributes
- Updates all cross-references: for=, href=#, url(#), filter=url(#)
- Strips CSS and HTML comments
- Collapses whitespace in CSS and HTML

Usage:
    python html_minify.py input.html -o output.html
    python html_minify.py input.html                       # prints to stdout
    python html_minify.py input.html -o output.html -m     # also print renaming map
    python html_minify.py input.html -o output.html -f     # skip variable inlining
    python html_minify.py input.html -o output.html -f -m  # fast mode + map

Options:
    input              Input HTML file
    -o, --output FILE  Output file (default: stdout)
    -m, --map          Print the renaming map to stderr
    -f, --fast         Skip constant variable inlining (faster, slightly larger output)
"""

import re
import sys
import argparse
import string
import math


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


# ---------------------------------------------------------------------------
# Constant CSS variable inlining & calc() evaluation
# ---------------------------------------------------------------------------

def find_var_declarations(css_text):
    """Find all --var: value declarations across CSS text.
    Returns dict of var_name -> list of values (multiple means redefined)."""
    cleaned = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    cleaned = re.sub(r'"[^"]*"', '""', cleaned)
    cleaned = re.sub(r"'[^']*'", "''", cleaned)

    declarations = {}
    for m in re.finditer(r'(--[\w-]+)\s*:\s*([^;{}]+?)\s*(?:;|(?=\}))', cleaned):
        name = m.group(1)
        value = m.group(2).strip()
        declarations.setdefault(name, []).append(value)
    return declarations


def identify_constants(declarations):
    """Return {var_name: value} for variables defined exactly once
    with a simple constant value (no var() references)."""
    constants = {}
    for name, values in declarations.items():
        if len(values) == 1 and 'var(' not in values[0]:
            constants[name] = values[0]
    return constants


def resolve_var_chains(constants, declarations):
    """Resolve chains like --a: var(--b) where --b is already a known constant."""
    changed = True
    for _ in range(20):  # safety cap
        if not changed:
            break
        changed = False
        for name, values in declarations.items():
            if len(values) != 1 or name in constants:
                continue
            value = values[0]

            def _replace(m):
                ref = m.group(1)
                return constants[ref] if ref in constants else m.group(0)

            resolved = re.sub(r'var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)', _replace, value)
            if 'var(' not in resolved:
                constants[name] = resolved
                changed = True
    return constants


def count_var_usages(css_text, html_text, var_name):
    """Count how many times var(--name) appears across CSS and HTML."""
    pattern = r'var\(\s*' + re.escape(var_name) + r'\s*(?:,[^)]*)?\)'
    return len(re.findall(pattern, css_text)) + len(re.findall(pattern, html_text))


def should_inline_var(var_name, value, usage_count):
    """Return True if inlining saves bytes vs keeping the (renamed) variable.

    After renaming the variable would be something like --a (4 chars).
    Keeping it costs:  declaration  +  N * 'var(--a)'  =  ~(4+2+len(value))  +  N*9
    Inlining costs:    N * len(value)
    """
    short_var_len = 4  # e.g. --a (conservative; could be --aa etc)
    decl_cost = short_var_len + 1 + len(value) + 1  # --a:value;
    keep_cost = decl_cost + usage_count * (4 + short_var_len + 1)  # var(--a)
    inline_cost = usage_count * len(value)
    return inline_cost <= keep_cost


def inline_var_in_css(css, var_name, value):
    """Replace var(--name) with value in CSS text."""
    pattern = r'var\(\s*' + re.escape(var_name) + r'\s*(?:,[^)]*)?\)'
    return re.sub(pattern, value, css)


def remove_var_declaration(css, var_name):
    """Remove a --var: value; declaration from CSS.  Also removes the
    surrounding rule block if it becomes empty."""
    # Remove the declaration line (with optional trailing whitespace / semicolon)
    pattern = re.escape(var_name) + r'\s*:\s*[^;{}]+?\s*;[ \t]*'
    css = re.sub(pattern, '', css)
    # Also handle the last-property-no-semicolon case
    pattern2 = re.escape(var_name) + r'\s*:\s*[^;{}]+?\s*(?=\})'
    css = re.sub(pattern2, '', css)
    # Remove empty rule blocks:  selector { }
    css = re.sub(r'[^{};]+\{\s*\}', '', css)
    return css


# ----- calc() evaluator -----

_CALC_NUM = re.compile(
    r'(-?\d+\.?\d*(?:e[+-]?\d+)?)'
    r'(px|em|rem|%|vh|vw|vmin|vmax|deg|rad|turn|s|ms|fr|ch|ex|cm|mm|in|pt|pc)?',
    re.IGNORECASE,
)

def _tokenize_calc(expr):
    """Tokenize a calc expression into numbers (with units), ops, and parens."""
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c in ' \t\n':
            i += 1
            continue
        if c in '()':
            tokens.append(('PAREN', c, ''))
            i += 1
            continue
        if c in '+*/' or (c == '-' and tokens and tokens[-1][0] == 'NUM'):
            tokens.append(('OP', c, ''))
            i += 1
            continue
        m = _CALC_NUM.match(expr, i)
        if m:
            tokens.append(('NUM', float(m.group(1)), (m.group(2) or '').lower()))
            i = m.end()
            continue
        # unrecognised token → can't evaluate
        return None
    return tokens


def _unit_mul(u1, u2):
    if u1 and u2:
        return None  # can't multiply two units
    return u1 or u2


def _unit_div(u1, u2):
    if u2 and u1 != u2:
        return None
    if u1 == u2 and u1:
        return ''  # same unit cancels
    return u1


def _unit_add(u1, u2):
    if u1 == u2:
        return u1
    if not u1:
        return u2
    if not u2:
        return u1
    return None  # incompatible


def _parse_calc_expr(tokens, pos):
    """Parse additive expression (handles + and -)."""
    left_val, left_unit, pos = _parse_calc_term(tokens, pos)
    if left_val is None:
        return None, None, pos
    while pos < len(tokens) and tokens[pos][0] == 'OP' and tokens[pos][1] in '+-':
        op = tokens[pos][1]
        pos += 1
        right_val, right_unit, pos = _parse_calc_term(tokens, pos)
        if right_val is None:
            return None, None, pos
        unit = _unit_add(left_unit, right_unit)
        if unit is None:
            return None, None, pos
        left_val = left_val + right_val if op == '+' else left_val - right_val
        left_unit = unit
    return left_val, left_unit, pos


def _parse_calc_term(tokens, pos):
    """Parse multiplicative expression (handles * and /)."""
    left_val, left_unit, pos = _parse_calc_atom(tokens, pos)
    if left_val is None:
        return None, None, pos
    while pos < len(tokens) and tokens[pos][0] == 'OP' and tokens[pos][1] in '*/':
        op = tokens[pos][1]
        pos += 1
        right_val, right_unit, pos = _parse_calc_atom(tokens, pos)
        if right_val is None:
            return None, None, pos
        if op == '*':
            unit = _unit_mul(left_unit, right_unit)
            if unit is None:
                return None, None, pos
            left_val *= right_val
        else:
            if right_val == 0:
                return None, None, pos
            unit = _unit_div(left_unit, right_unit)
            if unit is None:
                return None, None, pos
            left_val /= right_val
        left_unit = unit
    return left_val, left_unit, pos


def _parse_calc_atom(tokens, pos):
    """Parse a number or parenthesised sub-expression."""
    if pos >= len(tokens):
        return None, None, pos
    tok = tokens[pos]
    if tok[0] == 'NUM':
        return tok[1], tok[2], pos + 1
    if tok[0] == 'PAREN' and tok[1] == '(':
        val, unit, pos = _parse_calc_expr(tokens, pos + 1)
        if val is None or pos >= len(tokens) or tokens[pos][1] != ')':
            return None, None, pos
        return val, unit, pos + 1
    return None, None, pos


def _format_calc_value(val, unit):
    """Format a numeric result nicely."""
    if val == int(val):
        s = str(int(val))
    else:
        s = f'{val:.6g}'
    if val == 0:
        return '0'
    return s + unit


def try_evaluate_calc(calc_content):
    """Try to evaluate a calc() body to a simple value.
    Returns the simplified string, or None if it can't be fully resolved."""
    tokens = _tokenize_calc(calc_content)
    if tokens is None:
        return None
    val, unit, pos = _parse_calc_expr(tokens, 0)
    if val is None or pos != len(tokens):
        return None
    return _format_calc_value(val, unit)


def simplify_all_calc(text):
    """Find all calc(...) in text and replace with evaluated value where possible."""
    def _replace_calc(m):
        body = m.group(1)
        # Handle nested calc() – flatten first
        body = re.sub(r'calc\(', '(', body)
        result = try_evaluate_calc(body)
        return result if result is not None else m.group(0)

    return re.sub(r'calc\(([^)]+(?:\([^)]*\))*[^)]*)\)', _replace_calc, text)


def inline_constant_vars(style_blocks, html_content):
    """Inline constant CSS variables and evaluate resulting calc() expressions.
    Returns updated (style_blocks, html_content, inlined_map)."""
    print("Scanning for constant CSS variables...", file=sys.stderr)
    all_css = '\n'.join(b['css'] for b in style_blocks)

    declarations = find_var_declarations(all_css)
    constants = identify_constants(declarations)
    constants = resolve_var_chains(constants, declarations)

    if not constants:
        print("No constant CSS variables to inline.", file=sys.stderr)
        print("No calc() expressions to evaluate.", file=sys.stderr)
        return style_blocks, html_content, {}

    # Decide which to inline based on size savings
    to_inline = {}
    for var_name, value in constants.items():
        usage = count_var_usages(all_css, html_content, var_name)
        if usage > 0 and should_inline_var(var_name, value, usage):
            to_inline[var_name] = value

    if not to_inline:
        print("No constant CSS variables to inline.", file=sys.stderr)
        print("No calc() expressions to evaluate.", file=sys.stderr)
        return style_blocks, html_content, {}

    print(f"Inlining {len(to_inline)} constant CSS variable{'s' if len(to_inline) != 1 else ''}...  0%", end="", file=sys.stderr)

    # Inline in CSS blocks (longest var names first to avoid partial matches)
    total_ops = len(style_blocks) * len(to_inline)
    done_ops = 0
    sorted_inline = sorted(to_inline.items(), key=lambda x: -len(x[0]))
    for b in style_blocks:
        css = b['css']
        for var_name, value in sorted_inline:
            css = inline_var_in_css(css, var_name, value)
            css = remove_var_declaration(css, var_name)
            done_ops += 1
            pct = done_ops * 100 // total_ops // 10 * 10
            print(f"\b\b\b{pct:2d}%", end="", flush=True, file=sys.stderr)
        css = simplify_all_calc(css)
        b['css'] = css

    print(file=sys.stderr)

    # Rebuild html_content with updated CSS blocks
    for block in reversed(style_blocks):
        replacement = block['open_tag'] + block['css'] + block['close_tag']
        html_content = html_content[:block['start']] + replacement + html_content[block['end']:]

    # Inline in HTML (inline style= attributes etc.)
    for var_name, value in sorted(to_inline.items(), key=lambda x: -len(x[0])):
        pattern = r'var\(\s*' + re.escape(var_name) + r'\s*(?:,[^)]*)?\)'
        html_content = re.sub(pattern, value, html_content)

    print("Evaluating calc() expressions...", file=sys.stderr)
    html_content = simplify_all_calc(html_content)

    # Re-extract blocks from rebuilt HTML
    style_blocks = extract_style_blocks(html_content)

    return style_blocks, html_content, to_inline


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


def resolve_undefined_var_fallbacks(style_blocks, html_content):
    """Replace var(--name, fallback) with fallback when --name is never defined."""
    all_css = '\n'.join(b['css'] for b in style_blocks)
    declared = set(find_var_declarations(all_css).keys())

    def _replace_if_undefined(m):
        var_name = m.group(1)
        fallback = m.group(2)
        if var_name not in declared and fallback is not None:
            return fallback.strip()
        return m.group(0)

    pattern = r'var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)'

    for b in style_blocks:
        b['css'] = re.sub(pattern, _replace_if_undefined, b['css'])

    # Rebuild HTML with updated CSS
    for block in reversed(style_blocks):
        replacement = block['open_tag'] + block['css'] + block['close_tag']
        html_content = html_content[:block['start']] + replacement + html_content[block['end']:]

    # Also in inline styles
    html_content = re.sub(pattern, _replace_if_undefined, html_content)

    style_blocks = extract_style_blocks(html_content)
    return style_blocks, html_content


def shorten_hex_colors(text):
    """Shorten 6-digit hex colors to 3-digit where possible. #aabbcc -> #abc"""
    def _shorten(m):
        h = m.group(1)
        if h[0] == h[1] and h[2] == h[3] and h[4] == h[5]:
            return '#' + h[0] + h[2] + h[4]
        return m.group(0)
    return re.sub(r'#([0-9a-fA-F]{6})\b', _shorten, text)


def shorten_zero_units(text):
    """Remove units from zero values in CSS. 0px -> 0, 0em -> 0, etc."""
    return re.sub(r'\b0(px|em|rem|%|vh|vw|vmin|vmax|pt|pc|cm|mm|in|ex|ch)\b', '0', text)


def remove_unnecessary_quotes(html):
    """Remove quotes from attribute values where they're not needed.
    HTML spec allows unquoted values that don't contain spaces, quotes, =, <, >, or backticks.
    Preserves quotes when the value immediately precedes /> to avoid the HTML5 parser
    consuming the / as part of an unquoted attribute value.
    Protects url(...) content from being modified (data URIs contain embedded attributes)."""
    # Temporarily replace url(...) content to protect embedded attributes
    url_placeholders = []
    def _protect_url(m):
        url_placeholders.append(m.group(0))
        return f'__URL_PLACEHOLDER_{len(url_placeholders) - 1}__'
    protected = re.sub(r'url\([^)]*\)', _protect_url, html)

    def _unquote(m):
        before = m.group(1)  # attr=
        quote = m.group(2)
        value = m.group(3)
        after = m.group(4)   # character(s) after closing quote
        if re.match(r'^[a-zA-Z0-9._-]+$', value):
            # Don't unquote if immediately followed by /> (self-closing tag)
            # because the / would be parsed as part of the unquoted value
            if after == '/>':
                return m.group(0)
            return before + value + after
        return m.group(0)
    result = re.sub(r'(\w+=)(["\'])([^"\']*)\2(/>|)', _unquote, protected)

    # Restore url(...) content
    for i, original in enumerate(url_placeholders):
        result = result.replace(f'__URL_PLACEHOLDER_{i}__', original)
    return result


TAG_RENAMES = {
    'div': 'd',
    'span': 't',
}

# CSS needed to restore default behavior of renamed tags
TAG_RENAME_CSS = {
    'div': 'd{display:block}',
}


def rename_tags(html):
    """Rename generic HTML tags (div->d, span->t) and inject compensating CSS."""
    renamed_any = {}
    for old_tag, new_tag in TAG_RENAMES.items():
        # Opening tags: <div ...> or <div>
        pattern = re.compile(r'<' + old_tag + r'(\s|>|/>)', re.IGNORECASE)
        if pattern.search(html):
            html = pattern.sub('<' + new_tag + r'\1', html)
            renamed_any[old_tag] = new_tag
        # Closing tags: </div>
        pattern_close = re.compile(r'</' + old_tag + r'>', re.IGNORECASE)
        html = pattern_close.sub('</' + new_tag + '>', html)

    # Inject compensating CSS rules into the first <style> block
    if renamed_any:
        extra_css = ''.join(
            TAG_RENAME_CSS[old] for old in renamed_any if old in TAG_RENAME_CSS
        )
        if extra_css:
            # Also rename tags in existing CSS selectors
            for old_tag, new_tag in renamed_any.items():
                # Replace tag selectors in CSS (word boundary aware)
                extra_css_already_uses_new = True  # we built it with new names

            html = re.sub(
                r'(<style[^>]*>)',
                r'\1' + extra_css,
                html, count=1, flags=re.IGNORECASE
            )

    # Rename tag selectors in CSS style blocks
    style_pattern = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.DOTALL | re.IGNORECASE)
    def _rename_in_style(m):
        css = m.group(2)
        for old_tag, new_tag in renamed_any.items():
            # Replace tag selectors — match old_tag when used as a selector
            # (at start, after space/comma/>/+/~, before {/./#!/[/:/space/,/>/+/~)
            css = re.sub(
                r'(?<![a-zA-Z0-9_-])' + old_tag + r'(?=[{\s.#\[:>,+~)!;]|$)',
                new_tag, css
            )
        return m.group(1) + css + m.group(3)

    html = style_pattern.sub(_rename_in_style, html)

    return html, renamed_any


def process(html_content, fast=False):
    """Main processing pipeline."""
    style_blocks = extract_style_blocks(html_content)
    inlined_map = {}

    if fast:
        print("Skipping constant variable inlining (fast mode).", file=sys.stderr)
    else:
        # Phase 0: inline constant CSS variables & evaluate calc()
        style_blocks, html_content, inlined_map = inline_constant_vars(style_blocks, html_content)

        # Phase 0b: resolve undefined var() references that have fallbacks
        print("Resolving undefined variable fallbacks...", file=sys.stderr)
        style_blocks, html_content = resolve_undefined_var_fallbacks(style_blocks, html_content)

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
    print("Shortening CSS variable names...", file=sys.stderr)
    result = html_content
    for block in reversed(style_blocks):
        css = block['css']
        css = rename_in_css(css, class_map, id_map, var_map)
        css = minify_css(css)
        replacement = block['open_tag'] + css + block['close_tag']
        result = result[:block['start']] + replacement + result[block['end']:]

    # Rename in HTML
    print("Shortening class names and IDs...", file=sys.stderr)
    result = rename_in_html(result, class_map, id_map, var_map)

    # Shorten colors and units in inline styles
    print("Shortening colors and zero values...", file=sys.stderr)
    result = shorten_hex_colors(result)
    result = shorten_zero_units(result)

    # Rename tags (div->d, span->t)
    print("Shortening tag names...", file=sys.stderr)
    result, tag_map = rename_tags(result)

    # Remove unnecessary quotes from attributes
    print("Removing unnecessary quotes...", file=sys.stderr)
    result = remove_unnecessary_quotes(result)

    # Minify HTML whitespace
    print("Collapsing whitespace...", file=sys.stderr)
    result = minify_html_whitespace(result)

    return result, class_map, id_map, var_map, inlined_map


def main():
    sys.stderr.reconfigure(write_through=True)
    parser = argparse.ArgumentParser(description='Minify HTML with class/ID renaming')
    parser.add_argument('input', help='Input HTML file')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-m', '--map', action='store_true',
                        help='Print the renaming map to stderr')
    parser.add_argument('-f', '--fast', action='store_true',
                        help='Skip constant variable inlining (faster)')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        html_content = f.read()

    result, class_map, id_map, var_map, inlined_map = process(html_content, fast=args.fast)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        orig_size = len(html_content.encode('utf-8'))
        new_size = len(result.encode('utf-8'))
        saving = (1 - new_size / orig_size) * 100 if orig_size else 0
        print(file=sys.stderr)
        print(f"Original: {orig_size} bytes", file=sys.stderr)
        print(f"Minified: {new_size} bytes", file=sys.stderr)
        print(f"Saved:    {saving:.1f}%", file=sys.stderr)
    else:
        print(result)

    if args.map:
        if inlined_map:
            print("\nInlined CSS variables:", file=sys.stderr)
            for old, val in sorted(inlined_map.items()):
                print(f"  {old}: {val}  (inlined)", file=sys.stderr)
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
