#!/usr/bin/env python3
"""Build the static site from src/ into the repository root.

Run from anywhere:  python3 src/build.py
Every page is written as <path>/index.html so GitHub Pages serves clean URLs.
"""
import datetime
import html
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
SITE = 'https://joshnotes.github.io'
TEMPLATE = (SRC / 'templates' / 'base.html').read_text()


def read_doc(path):
    text = path.read_text()
    m = re.match(r'<!--meta\s*(\{.*?\})\s*-->\s*', text, re.S)
    if not m:
        raise SystemExit(f'{path}: missing <!--meta {{...}} --> block')
    return json.loads(m.group(1)), text[m.end():]


def esc(s):
    return html.escape(s, quote=True)


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def lower_first(s):
    return s[0].lower() + s[1:] if re.match(r'^[A-Z][a-z]', s) else s


def share_image(path, alt):
    """og:image tags for the page's preview image, drawn by src/og.py, if it has one."""
    key = path.strip('/').replace('/', '-') or 'home'
    if not (ROOT / 'assets' / 'og' / f'{key}.png').exists():
        return ''
    return (f'<meta property="og:image" content="{SITE}/assets/og/{key}.png">\n'
            '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="627">\n'
            f'<meta property="og:image:alt" content="{esc(alt)}">\n<meta name="twitter:card" content="summary_large_image">\n')


import hashlib


def asset_version(name):
    """A short fingerprint of an asset's content, so browsers fetch it again whenever it changes."""
    return hashlib.md5((ROOT / 'assets' / name).read_bytes()).hexdigest()[:8]


ASSETS = ('site.css', 'site.js', 'wisdom.css', 'wisdom.js')


def versioned(html_text):
    for name in ASSETS:
        if (ROOT / 'assets' / name).exists():
            html_text = html_text.replace(f'/assets/{name}"', f'/assets/{name}?v={asset_version(name)}"')
    return html_text


def page(meta, content, nav='', og_type='website', og_extra='', body_class=''):
    path = meta['path']
    canonical = SITE + (path if path != '/404.html' else '/')
    og_extra = share_image(path, meta['title']) + og_extra
    cur = ' aria-current="page"'
    out = TEMPLATE
    for key, val in {
        '{{TITLE}}': esc(meta.get('page_title') or f"{meta['title']} | joshnotes"),
        '{{OG_TITLE}}': esc(meta['title']),
        '{{DESCRIPTION}}': esc(meta['dek']),
        '{{CANONICAL}}': canonical,
        '{{OG_TYPE}}': og_type,
        '{{OG_EXTRA}}': og_extra + ('<meta name="robots" content="noindex">\n' if meta.get('noindex') else ''),
        '{{NAV_HOME}}': cur if nav == 'home' else '',
        '{{NAV_WISDOM}}': cur if nav == 'wisdom' else '',
        '{{NAV_NOTES}}': cur if nav == 'notes' else '',
        '{{NAV_RESEARCH}}': cur if nav == 'research' else '',
        '{{NAV_ABOUT}}': cur if nav == 'about' else '',
        '{{BODY_CLASS}}': body_class,
        '{{CONTENT}}': content,
    }.items():
        out = out.replace(key, val)
    return versioned(out)


def write(rel_path, text):
    target = ROOT / rel_path.lstrip('/')
    if rel_path.endswith('/'):
        target = target / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


def load_articles(section):
    items = []
    for f in sorted((SRC / 'content' / section).glob('*.html')):
        meta, body = read_doc(f)
        meta['path'] = f'/{section}/{meta["slug"]}/'
        items.append((meta, body))
    items.sort(key=lambda mb: (mb[0].get('order', 99), mb[0]['date']))
    return items


PHOTOS = json.loads((SRC / 'photos.json').read_text()) if (SRC / 'photos.json').exists() else {}


def lead_photo(meta):
    """The piece's photo, black and white until hovered or tapped, with its credit underneath."""
    key = meta['path'].strip('/').replace('/', '-')
    ph = PHOTOS.get(key)
    if not ph or not (ROOT / 'assets' / 'img' / 'lead' / f'{key}-1200.webp').exists():
        return ''
    lic = ph['license']
    lic_html = f'<a href="{esc(ph["license_url"])}">{esc(lic)}</a>' if ph.get('license_url') else esc(lic.lower() if lic == 'Public domain' else lic)
    changed = ', cropped' if lic.startswith('CC BY') else ''
    return (f'<figure class="lead photo"><img src="/assets/img/lead/{key}-1200.webp" '
            f'srcset="/assets/img/lead/{key}-600.webp 600w, /assets/img/lead/{key}-1200.webp 1200w" '
            f'sizes="(max-width: 640px) 100vw, 880px" width="{ph["w"]}" height="{ph["h"]}" alt="{esc(ph["alt"])}">'
            f'<figcaption>Photo: <a href="{esc(ph["page"])}">{esc(ph["artist"])}</a>, {lic_html}{changed}</figcaption></figure>\n')


def article_html(meta, body, prev_item, next_item):
    section_name = 'Notes' if meta['section'] == 'notes' else 'Research'
    section_url = '/notes/' if meta['section'] == 'notes' else '/research/'
    pager = '<nav class="pager" aria-label="More in ' + section_name + '">'
    if prev_item:
        pager += f'<a class="nextup" href="{prev_item["path"]}"><p class="kick">Previous</p><h3>{esc(prev_item["title"])}</h3></a>'
    if next_item:
        pager += f'<a class="nextup" href="{next_item["path"]}"><p class="kick">Next</p><h3>{esc(next_item["title"])}</h3></a>'
    pager += '</nav>'
    return f'''<article class="artwrap gut">
  <p class="crumbs"><a href="{section_url}">{section_name}</a><span>/</span><span>{esc(meta["kick"])}</span></p>
  <h1>{esc(meta["title"])}</h1>
  <p class="dek">{esc(meta["dek"])}</p>
  <p class="byline"><b>Joshuva Johnson</b><time datetime="{meta["date"]}">{nice_date(meta["date"])}</time></p>
{body.replace('<div class="prose">', lead_photo(meta) + '<div class="prose">', 1)}
  {pager}
</article>'''


def ticker(company, body):
    """The ticker the pitch gives right after the company's name, as in 'Eaton (ETN)'."""
    m = re.search(re.escape(company) + r'[^(<]{0,40}\(([A-Z]{1,5})\)', body)
    return m.group(1) if m else ''


def pitches(research):
    """One dict per stock pitch, read from the pitch's key-figure strip."""
    out = []
    for meta, body in research:
        if meta.get('kind') != 'pitch':
            continue
        m = re.search(r'<div class="kf[^"]*">(.*?)</div></div>', body, re.S)
        if not m:
            continue
        cells = re.findall(r'<b>(.*?)</b><span>(.*?)</span>', m.group(1))
        if len(cells) < 4:
            continue
        (rating, _), (value, _), (gap, _), (price, price_label) = cells[:4]
        company = meta.get('company') or meta['title'].split(':')[0].split(' after ')[0]  # set "company" in the pitch's meta
        out.append({'meta': meta, 'company': company, 'ticker': ticker(company, body), 'rating': rating, 'value': value,
                    'gap': gap, 'price': price, 'as_of': re.sub(r'^Price (at )?', '', price_label)})
    return out


def pitch_table(research):
    """Ratings table for the stock pitches, read from each pitch's key-figure strip."""
    ps = pitches(research)
    as_of = ps[0]['as_of'] if ps else ''
    rows = [f'<tr><th scope="row"><a href="{p["meta"]["path"]}">{esc(p["company"])}</a><span>{p["ticker"] + ", " if p["ticker"] else ""}{esc(p["meta"]["topic"])}</span></th>'
            f'<td>{p["rating"]}</td><td class="n">{p["value"]}</td><td class="n hide-s">{p["price"]}</td><td class="n">{p["gap"]}</td></tr>' for p in ps]
    if not rows:
        return ''
    return ('<div class="ratings"><table>\n'
            '<thead><tr><th scope="col">Company</th><th scope="col">Rating</th><th scope="col" class="n">Value per share</th>'
            '<th scope="col" class="n hide-s">Price</th><th scope="col" class="n">Value vs price</th></tr></thead>\n<tbody>\n'
            + '\n'.join(rows) + '\n</tbody></table>\n'
            f'<p class="fnote">Prices at the {esc(as_of)}.</p></div>')


def logo_tiles(items):
    """About: one tile per organisation. The logo (assets/img/logos/<slug>.webp, .svg or .png) is black and white until
    a mouse is over the tile or it is tapped; then the whole tile takes the brand colour (bg), its text turns fg, and the
    logo shows knocked out in white or black, or in its own colours ("on": white / black / none).
    Each position is a title with its years underneath. Logo sources are recorded in pages/about.html."""
    knock = {'white': 'brightness(0) invert(1)', 'black': 'brightness(0)', 'none': 'none'}
    out = []
    for o in items:
        path = next((f'img/logos/{o["slug"]}.{ext}' for ext in ('svg', 'webp', 'png')
                     if (ROOT / 'assets' / 'img' / 'logos' / f'{o["slug"]}.{ext}').exists()), '')
        size = f' style="--h:{o["h"]}px"' if o.get('h') else ''  # per-logo height, so marks look about the same size
        mark = (f'<img src="/assets/{path}?v={asset_version(path)}" alt="{esc(o["name"])}"{size} loading="lazy" decoding="async">'
                if path else esc(o['name']))
        arrow = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 11.5l7-7M5.5 4.5h6v6"/></svg>'

        def role(r):
            title, when, url = (list(r) + ['', ''])[:3]
            head = (f'<a class="lg-rl" href="{esc(url)}" target="_blank" rel="noopener" aria-label="{esc(o["name"])} {esc(title)}: view the credential '
                    f'(opens in a new tab)"><b>{esc(title)}</b>{arrow}</a>') if url else f'<b>{esc(title)}</b>'
            return f'<span class="lg-pos">{head}' + (f'<span><span class="nw">{esc(when)}</span></span>' if when else '') + '</span>'
        roles = ''.join(role(r) for r in o.get('roles', []))  # a role with its own link: [title, years, url]
        # A credential link makes the whole tile clickable (opens in a new tab), with a small arrow shown on hover.
        cover = ''
        if o.get('url'):
            what = o['roles'][0][0] if o.get('roles') else o['name']
            label = what if o['name'].lower() in what.lower() else f'{o["name"]} {what}'
            cover = (f'<a class="lg-cover" href="{esc(o["url"])}" target="_blank" rel="noopener" '
                     f'aria-label="{esc(label)}: view the credential (opens in a new tab)">'
                     '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 11.5l7-7M5.5 4.5h6v6"/></svg></a>')
        style = f'--c:{o["bg"]};--f:{o["fg"]};--on:{knock[o.get("on", "none")]}'
        out.append(f'      <li class="lg{" has-img" if path else " no-img"}{" linked" if cover else ""}" style="{style}"><span class="lg-mark">{mark}</span>'
                   f'<span class="lg-roles">{roles}</span>{cover}</li>')
    return '\n'.join(out)


def ratings_compact(research):
    """The home page's narrow ratings table: company, rating, and how far value sits from price."""
    ps = pitches(research)
    if not ps:
        return ''
    rows = '\n'.join(f'<tr><th scope="row"><a href="{p["meta"]["path"]}">{esc(p["company"])}</a><span>{p["ticker"]}</span></th>'
                     f'<td>{p["rating"]}</td><td class="n">{p["gap"]}</td></tr>' for p in ps)
    return ('<table class="rt">\n<thead><tr><th scope="col">Company</th><th scope="col">Rating</th>'
            '<th scope="col" class="n">Value vs price</th></tr></thead>\n'
            f'<tbody>\n{rows}\n</tbody></table>\n<p class="fnote">Prices at the {esc(ps[0]["as_of"])}.</p>')


# ---------- Home: the map of sectors and companies I follow ----------
# The list itself lives in pages/home.html (meta "watchlist"). This sets where things sit.
# at:   sector centre and where its name goes (n, s, e, w of the square)
# fan:  angles its companies fan out at, in degrees clockwise from 3 o'clock
# side: where a link's label sits next to its dot
MAP_LAYOUTS = {
    'wide': {'w': 720, 'h': 400, 'r': 66, 'font': 13,
             'at': {'metals': (130, 286, 's'), 'energy': (250, 106, 'w'), 'computing': (420, 206, 'e'),
                    'defense': (590, 106, 'e'), 'healthcare': (590, 306, 'ne')},
             'fan': {'metals': [40, 140, -130], 'energy': [-150, -90, -30, 60], 'computing': [150, -90, 90],
                     'defense': [-100, -40, 40], 'healthcare': [10, 70, 130]},
             'side': {'copper': 'e', 'power': 'ne', 'pltr': 'nw', 'drugs': 'ne'}},
    'tall': {'w': 380, 'h': 640, 'r': 58, 'font': 14,
             'at': {'metals': (110, 80, 'ne'), 'energy': (250, 215, 'e'), 'computing': (190, 380, 'e'),
                    'defense': (290, 540, 'w'), 'healthcare': (110, 560, 'w')},
             'fan': {'metals': [-120, 180, 140], 'energy': [160, -100, -40, 50], 'computing': [180, -140, 90],
                     'defense': [-50, 30, 100], 'healthcare': [0, 60, 120]},
             'side': {'copper': 'w', 'power': 'e', 'pltr': 'e', 'drugs': 'w'}},
}


def and_join(items):
    items = list(items)
    if len(items) < 3:
        return ' and '.join(items)
    return ', '.join(items[:-1]) + ', and ' + items[-1]


def piece_label(url, pieces):
    """Link text for a company's or a link's piece: the pitch's rating, or the note's title."""
    p = pieces.get(url, {})
    return f'Stock pitch: {p["rating"]}' if p.get('rating') else p.get('title', 'Read it')


def side_of(deg):
    """Which side of a company's dot its ticker goes on, from the angle it fans out at."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return 'e' if c > 0.42 else 'w' if c < -0.42 else ('s' if s > 0 else 'n')


def label_at(x, y, side, gap, F):
    """Where a label's baseline starts, and its anchor, for a dot at (x, y) and text of size F."""
    d = gap * 0.75  # diagonal sides sit a little closer
    return {'n': (x, y - gap, 'middle'), 's': (x, y + gap + 0.75 * F, 'middle'),
            'e': (x + gap, y + 0.35 * F, 'start'), 'w': (x - gap, y + 0.35 * F, 'end'),
            'ne': (x + d, y - d, 'start'), 'nw': (x - d, y - d, 'end'),
            'se': (x + d, y + d + 0.75 * F, 'start'), 'sw': (x - d, y + d + 0.75 * F, 'end')}[side]


def map_geometry(watch, lay):
    """Every line, dot and label of the map in one layout. src/og.py draws the share image from this."""
    R, F = lay['r'], lay['font']
    pos = {k: (x, y) for k, (x, y, _) in lay['at'].items()}
    g = {'links': [], 'spokes': [], 'companies': [], 'sectors': []}
    for s in watch['sectors']:
        x, y = pos[s['id']]
        for c, deg in zip(s['companies'], lay['fan'][s['id']]):
            cx, cy = x + R * math.cos(math.radians(deg)), y + R * math.sin(math.radians(deg))
            g['spokes'].append((x, y, cx, cy))
            g['companies'].append({'x': cx, 'y': cy, 'piece': len(c) > 2, 'label': (*label_at(cx, cy, side_of(deg), 10, F), c[0])})
        g['sectors'].append({'x': x, 'y': y, 'label': (*label_at(x, y, lay['at'][s['id']][2], 16, F), s['name'].upper())})
    for b in watch['bridges']:
        (x1, y1), (x2, y2) = (pos[x] for x in b['between'])
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        text = b.get('ticker') or b['label'].upper()
        g['links'].append({'line': (x1, y1, x2, y2), 'x': mx, 'y': my, 'piece': bool(b.get('url')), 'ticker': bool(b.get('ticker')),
                           'label': (*label_at(mx, my, lay['side'][b['id']], 12, F), text)})
    return g


def watch_map(watch, pieces):
    """The connection map: an SVG for wide screens, one for phones, and the captions they share.
    Returns (html, css). The css lights up whatever belongs to the sector or link under the pointer."""
    sectors, bridges = watch['sectors'], watch['bridges']
    sid = {s['id']: s for s in sectors}
    near = {s['id']: [b for b in bridges if s['id'] in b['between']] for s in sectors}
    keys = [s['id'] for s in sectors] + [b['id'] for b in bridges]

    def toks(*groups):
        out = set()
        for g in groups:
            out.update([g] if isinstance(g, str) else g)
        return ' '.join(sorted(out))

    def sector_toks(s):
        return toks(s, *[[b['id'], *b['between']] for b in near[s]])

    def link(text, url):
        return f'<a href="{url}">{esc(text)}</a>' if url else esc(text)

    # Captions: one per sector, one per link, and the default.
    caps = ['<p class="wc wc-0">Interactive visual</p>']
    for s in sectors:
        names = [link(c[1], c[2] if len(c) > 2 else '') for c in s['companies']]
        names = [link(b['name'], b.get('url', '')) for b in near[s['id']] if b.get('ticker')] + names
        other = [f'to {esc(sid[[x for x in b["between"] if x != s["id"]][0]]["name"])} through {esc(b["via"])}' for b in near[s['id']]]
        caps.append(f'<p class="wc wc-{s["id"]}" id="wc-{s["id"]}"><b>{esc(s["name"])}:</b> {and_join(names)}.'
                    + (f' Linked {and_join(other)}.' if other else '') + '</p>')
    for b in bridges:
        a, c = (sid[x]['name'] for x in b['between'])
        head = b.get('name') or b['label']
        more = f' {link(piece_label(b["url"], pieces), b["url"])}.' if b.get('url') else ''
        caps.append(f'<p class="wc wc-{b["id"]}" id="wc-{b["id"]}"><b>{esc(head)}, between {esc(a)} and {esc(c)}:</b> {esc(b["text"])}{more}</p>')

    def svg(name, lay):
        W, H, R, F = lay['w'], lay['h'], lay['r'], lay['font']
        pos = {k: (x, y) for k, (x, y, _) in lay['at'].items()}
        lines, nodes, under = [], {}, []

        def label(x, y, side, text, cls, gap=10):
            tx, ty, anchor = label_at(x, y, side, gap, F)
            return f'<text class="{cls}" x="{tx:.0f}" y="{ty:.0f}" text-anchor="{anchor}">{esc(text)}</text>'

        for s in sectors:
            x, y = pos[s['id']]
            out = []
            for (c, deg) in zip(s['companies'], lay['fan'][s['id']]):
                cx, cy = x + R * math.cos(math.radians(deg)), y + R * math.sin(math.radians(deg))
                lines.append(f'<line class="x sp" data-s="{s["id"]}" x1="{x}" y1="{y}" x2="{cx:.1f}" y2="{cy:.1f}" pathLength="1"/>')
                under.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5"/>')
                url = c[2] if len(c) > 2 else ''
                inner = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.5"/>' + label(cx, cy, side_of(deg), c[0], 'tk')
                         + f'<title>{esc(c[1])}{": " + esc(piece_label(url, pieces)) if url else ""}</title>')
                if url:
                    out.append(f'<a class="x cn pc" href="{url}" data-s="{s["id"]}" data-k="{s["id"]}">{inner}</a>')
                else:
                    out.append(f'<g class="x cn" data-s="{s["id"]}" data-k="{s["id"]}">{inner}</g>')
            lx, ly, side = lay['at'][s['id']]
            under.append(f'<rect x="{x - 8}" y="{y - 8}" width="16" height="16"/>')
            out.append(f'<g class="x sn" data-s="{sector_toks(s["id"])}" data-k="{s["id"]}" tabindex="0" role="button" '
                       f'aria-pressed="false" aria-label="{esc(s["name"])}" aria-describedby="wc-{s["id"]}">'
                       f'<circle class="hit" cx="{x}" cy="{y}" r="22"/><rect x="{x - 7}" y="{y - 7}" width="14" height="14"/>'
                       + label(x, y, side, s['name'].upper(), 'snl', 16) + '</g>')
            nodes[s['id']] = out
        for b in bridges:
            (x1, y1), (x2, y2) = (pos[x] for x in b['between'])
            t = toks(b['id'], b['between'])
            lines.insert(0, f'<line class="x br" data-s="{t}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" pathLength="1"/>')
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            side = lay['side'][b['id']]
            text = b.get('ticker') or b['label']
            cls = 'tk' if b.get('ticker') else 'bll'
            under.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="9"/>')
            inner = (f'<circle class="halo" cx="{mx:.1f}" cy="{my:.1f}" r="9"/><circle cx="{mx:.1f}" cy="{my:.1f}" r="{5.5 if b.get("ticker") else 4.5}"/>'
                     + label(mx, my, side, text if b.get('ticker') else text.upper(), cls, 12) + f'<title>{esc(b.get("name") or b["label"])}</title>')
            if b.get('url'):
                nodes[b['id']] = [f'<a class="x bn pc" href="{b["url"]}" data-s="{t}" data-k="{b["id"]}" aria-describedby="wc-{b["id"]}">{inner}</a>']
            else:
                nodes[b['id']] = [f'<g class="x bn" data-s="{t}" data-k="{b["id"]}" tabindex="0" role="button" aria-pressed="false" '
                                  f'aria-label="{esc(b["label"])}" aria-describedby="wc-{b["id"]}">{inner}</g>']
        # Reading order: each sector, then any link whose two ends have both appeared.
        order, seen = [], set()
        for s in sectors:
            order.append(s['id'])
            seen.add(s['id'])
            order += [b['id'] for b in bridges if b['id'] not in order and set(b['between']) <= seen]
        body = '\n'.join(n for k in order for n in nodes[k])
        return (f'<svg class="wsvg wsvg-{name}" viewBox="0 0 {W} {H}" role="group" aria-label="Sectors and companies I follow" '
                f'style="--f:{F}px">\n<g class="lines">{"".join(lines)}</g>\n<g class="under" aria-hidden="true">{"".join(under)}</g>\n{body}\n</svg>')

    html_out = ('<figure class="wm">\n' + svg('wide', MAP_LAYOUTS['wide']) + '\n' + svg('tall', MAP_LAYOUTS['tall'])
                + '\n<figcaption class="wcap" aria-live="polite">' + ''.join(caps) + '</figcaption>\n</figure>')
    css = ''.join(f'.wm[data-on={k}] .x:not([data-s~={k}]){{opacity:.12}}.wm[data-on={k}] .wc-{k}{{visibility:visible}}' for k in keys)
    return html_out, f'<style>{css}</style>\n'


def main():
    built = []
    notes = load_articles('notes')
    research = load_articles('research')

    # Articles
    for items, nav in ((notes, 'notes'), (research, 'research')):
        for i, (meta, body) in enumerate(items):
            prev_item = items[i - 1][0] if i > 0 else None
            next_item = items[i + 1][0] if i + 1 < len(items) else None
            og_extra = f'<meta property="article:published_time" content="{meta["date"]}">\n<meta property="article:author" content="Joshuva Johnson">\n'
            built.append(write(meta['path'], page(meta, article_html(meta, body, prev_item, next_item), nav, 'article', og_extra, 'article')))

    # Home
    meta, content = read_doc(SRC / 'content' / 'pages' / 'home.html')
    lead = notes[0][0]
    pieces = {m['path']: {'title': m['title']} for m, _ in notes + research}
    for p in pitches(research):
        pieces[p['meta']['path']]['rating'] = p['rating']
    map_html, map_css = watch_map(meta['watchlist'], pieces)
    heads = lambda items: '\n'.join(f'        <li><a href="{m["path"]}">{esc(m["title"])}</a></li>' for m in items)
    content = (content.replace('{{LEAD_TITLE}}', esc(lead['title']))
               .replace('{{LEAD_URL}}', lead['path'])
               .replace('{{WATCH_MAP}}', map_html)
               .replace('{{RATINGS}}', ratings_compact(research))
               .replace('{{NOTES_HEADLINES}}', heads([m for m, _ in notes[1:]][:3]))  # three each; the arrow leads to the rest
               .replace('{{RESEARCH_HEADLINES}}', heads([m for m, _ in research if m.get('kind') != 'pitch'][:3])))
    # Old single-page links looked like /#a-eaton. Send them to the new pages.
    legacy = {'research': '/research/', 'about': '/about/', 'r-method': '/research/method/', 'library': '/research/', 'thoughts': '/notes/'}
    legacy.update({m['legacy']: m['path'] for m, _ in notes + research if m.get('legacy')})
    redirect = ('<script>(function(){var m=' + json.dumps(legacy, separators=(',', ':')) +
                ';function go(){var h=location.hash.slice(1);if(m[h])location.replace(m[h]);}'
                'go();addEventListener("hashchange",go);})();</script>\n')
    built.append(write('/', page(meta, content, 'home', og_extra=redirect + map_css, body_class='home')))

    # Notes index
    meta, content = read_doc(SRC / 'content' / 'pages' / 'notes.html')
    note_cards = '\n'.join(
        f'      <a class="cardlink" href="{m["path"]}"><div class="card"><h3>{esc(m["title"])}</h3><p class="dek">{esc(m["dek"])}</p></div></a>'
        for m, _ in notes)
    built.append(write('/notes/', page(meta, content.replace('{{NOTES_CARDS}}', note_cards), 'notes')))

    # The notes used to live under /thoughts/. Forward old links, keeping any #anchor.
    def forward(old, new, title):
        return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
                f'<title>{esc(title)} | joshnotes</title><link rel="canonical" href="{SITE}{new}">'
                f'<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url={new}">'
                f'<script>location.replace("{new}"+location.hash)</script></head>'
                f'<body><p>This page moved to <a href="{new}">{esc(title)}</a>.</p></body></html>\n')
    built.append(write('/thoughts/', forward('/thoughts/', '/notes/', 'Notes')))
    for m, _ in notes:
        built.append(write(f'/thoughts/{m["slug"]}/', forward(f'/thoughts/{m["slug"]}/', m['path'], m['title'])))

    # Research index
    meta, content = read_doc(SRC / 'content' / 'pages' / 'research.html')
    # The pitches are already in the ratings table, so the list below it holds everything else.
    rows = '\n'.join(
        f'      <a class="lrow" href="{m["path"]}"><h3>{esc(m["title"])}</h3><p>{esc(m["dek"])}</p></a>'
        for m, _ in research if m.get('kind') != 'pitch')
    content = (content.replace('{{RESEARCH_ROWS}}', rows)
               .replace('{{PITCH_TABLE}}', pitch_table(research)))
    built.append(write('/research/', page(meta, content, 'research')))

    # Daily Dose of Wisdom: a dark page of its own, with its own stylesheet and script.
    meta, content = read_doc(SRC / 'content' / 'pages' / 'wisdom.html')
    shows = meta['shows']
    tiles = []
    for i, s in enumerate(shows):  # evenly round the wheel, the first at 12 o'clock
        a = math.radians(-90 + i * 360 / len(shows))
        tiles.append(f'        <li class="wz-show" style="left:{50 + 43 * math.cos(a):.2f}%;top:{50 + 43 * math.sin(a):.2f}%">'
                     f'<span class="wz-up"><img src="{esc(s["art"])}/300x300bb.jpg" alt="{esc(s["name"])}" width="300" height="300" decoding="async"></span></li>')
    data = json.dumps([{k: s[k] for k in ('id', 'name', 'host', 'art', 'apple')} for s in shows],
                      separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    head = ('<link rel="preload" href="/assets/fonts/instrument-serif-latin-400-italic.woff2" as="font" type="font/woff2" crossorigin>\n'
            '<link rel="stylesheet" href="/assets/wisdom.css">\n'
            '<meta name="theme-color" content="#000000">\n'
            '<script>document.documentElement.classList.add("portal")</script>\n'
            '<script src="/assets/wisdom.js" defer></script>\n')
    content = content.replace('{{WZ_TILES}}', '\n'.join(tiles)).replace('{{WZ_DATA}}', data)
    built.append(write('/wisdom/', page(meta, content, 'wisdom', og_extra=head, body_class='wisdom')))

    # Method, About, 404
    for name, nav, body_class in (('method', 'research', 'method'), ('about', 'about', ''), ('404', '', 'page-404')):
        meta, content = read_doc(SRC / 'content' / 'pages' / f'{name}.html')
        if name == 'about':
            content = (content.replace('{{WORK_LOGOS}}', logo_tiles(meta['work'])).replace('{{EDU_LOGOS}}', logo_tiles(meta['education']))
                       .replace('{{CERT_LOGOS}}', logo_tiles(meta['certs'])))
        target = '/404.html' if name == '404' else meta['path']
        text = page(meta, content, nav, body_class=body_class)
        if name == '404':
            built.append(write_file('/404.html', text))
        else:
            built.append(write(target, text))

    # sitemap.xml, robots.txt, .nojekyll
    today = datetime.date.today().isoformat()
    urls = ['/', '/notes/', '/research/', '/research/method/', '/about/', '/wisdom/'] + [m['path'] for m, _ in notes + research]
    lastmod = {m['path']: m['date'] for m, _ in notes + research}
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f'  <url><loc>{SITE}{u}</loc><lastmod>{lastmod.get(u, today)}</lastmod></url>' for u in urls]
    sitemap.append('</urlset>')
    built.append(write_file('/sitemap.xml', '\n'.join(sitemap) + '\n'))
    built.append(write_file('/robots.txt', f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n'))
    built.append(write_file('/.nojekyll', ''))

    for p in built:
        print('built', p.relative_to(ROOT))


def write_file(rel_path, text):
    target = ROOT / rel_path.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


if __name__ == '__main__':
    main()
