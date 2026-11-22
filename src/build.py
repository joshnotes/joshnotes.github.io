#!/usr/bin/env python3
"""Build the static site from src/ into the repository root.

Run from anywhere:  python3 src/build.py
Every page is written as <path>/index.html so GitHub Pages serves clean URLs.
"""
import datetime
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
SITE = 'https://joshuvajohnson.github.io'
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


def page(meta, content, nav='', og_type='website', og_extra='', body_class=''):
    path = meta['path']
    canonical = SITE + (path if path != '/404.html' else '/')
    og_extra = share_image(path, meta['title']) + og_extra
    cur = ' aria-current="page"'
    out = TEMPLATE
    for key, val in {
        '{{TITLE}}': esc(meta.get('page_title') or f"{meta['title']} | Joshuva Johnson"),
        '{{OG_TITLE}}': esc(meta['title']),
        '{{DESCRIPTION}}': esc(meta['dek']),
        '{{CANONICAL}}': canonical,
        '{{OG_TYPE}}': og_type,
        '{{OG_EXTRA}}': og_extra + ('<meta name="robots" content="noindex">\n' if meta.get('noindex') else ''),
        '{{NAV_THOUGHTS}}': cur if nav == 'thoughts' else '',
        '{{NAV_RESEARCH}}': cur if nav == 'research' else '',
        '{{NAV_ABOUT}}': cur if nav == 'about' else '',
        '{{BODY_CLASS}}': body_class,
        '{{CONTENT}}': content,
    }.items():
        out = out.replace(key, val)
    return out


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


def article_html(meta, body, prev_item, next_item):
    section_name = 'Thoughts' if meta['section'] == 'thoughts' else 'Research'
    section_url = '/' if meta['section'] == 'thoughts' else '/research/'
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
{body}
  {pager}
</article>'''


def pitch_table(research):
    """Ratings table for the stock pitches, read from each pitch's key-figure strip."""
    rows, as_of = [], ''
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
        as_of = as_of or re.sub(r'^Price (at )?', '', price_label)
        company = meta['title'].split(':')[0].split(' after ')[0]
        rows.append(f'<tr><th scope="row"><a href="{meta["path"]}">{esc(company)}</a><span>{esc(meta["topic"])}</span></th>'
                    f'<td>{rating}</td><td class="n">{value}</td><td class="n hide-s">{price}</td><td class="n">{gap}</td></tr>')
    if not rows:
        return ''
    return ('<div class="ratings"><table>\n'
            '<thead><tr><th scope="col">Company</th><th scope="col">Rating</th><th scope="col" class="n">Value per share</th>'
            '<th scope="col" class="n hide-s">Price</th><th scope="col" class="n">Value vs price</th></tr></thead>\n<tbody>\n'
            + '\n'.join(rows) + '\n</tbody></table>\n'
            f'<p class="fnote">Prices at the {esc(as_of)}. Values are probability-weighted, from each pitch. Personal research, not investment advice.</p></div>')


def main():
    built = []
    thoughts = load_articles('thoughts')
    research = load_articles('research')

    # Articles
    for items, nav in ((thoughts, 'thoughts'), (research, 'research')):
        for i, (meta, body) in enumerate(items):
            prev_item = items[i - 1][0] if i > 0 else None
            next_item = items[i + 1][0] if i + 1 < len(items) else None
            og_extra = f'<meta property="article:published_time" content="{meta["date"]}">\n<meta property="article:author" content="Joshuva Johnson">\n'
            built.append(write(meta['path'], page(meta, article_html(meta, body, prev_item, next_item), nav, 'article', og_extra, 'article')))

    # Home (ThoughtsbyJosh)
    meta, content = read_doc(SRC / 'content' / 'pages' / 'home.html')
    lead, rest = thoughts[0][0], [m for m, _ in thoughts[1:]]
    cards = '\n'.join(
        f'      <a class="cardlink" href="{m["path"]}"><div class="card"><p class="kick">{esc(m["topic"])}</p><h3>{esc(m["title"])}</h3><p class="dek">{esc(m["dek"])}</p><p class="meta"><span>{nice_date(m["date"])}</span></p></div></a>'
        for m in rest)
    content = (content.replace('{{LEAD_TITLE}}', esc(lead['title']))
               .replace('{{LEAD_DEK}}', esc(lead['dek']))
               .replace('{{LEAD_META}}', f'<span>{esc(lead["topic"])}</span><span>{nice_date(lead["date"])}</span>')
               .replace('{{LEAD_URL}}', lead['path'])
               .replace('{{THOUGHTS_CARDS}}', cards)
               .replace('{{PITCH_TABLE}}', pitch_table(research)))
    # Old single-page links looked like /#a-eaton. Send them to the new pages.
    legacy = {'research': '/research/', 'about': '/about/', 'r-method': '/research/method/', 'library': '/research/'}
    legacy.update({m['legacy']: m['path'] for m, _ in thoughts + research if m.get('legacy')})
    redirect = ('<script>(function(){var m=' + json.dumps(legacy, separators=(',', ':')) +
                ';function go(){var h=location.hash.slice(1);if(m[h])location.replace(m[h]);else if(h==="thoughts")history.replaceState(null,"","/");}'
                'go();addEventListener("hashchange",go);})();</script>\n')
    built.append(write('/', page(meta, content, 'thoughts', og_extra=redirect, body_class='home')))

    # /thoughts/ points at the home page, which is the Thoughts index
    built.append(write('/thoughts/', '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Thoughts | Joshuva Johnson</title>'
                       f'<link rel="canonical" href="{SITE}/"><meta http-equiv="refresh" content="0; url=/"><meta name="robots" content="noindex"></head>'
                       '<body><p>Thoughts live on the <a href="/">home page</a>.</p></body></html>\n'))

    # Research index
    meta, content = read_doc(SRC / 'content' / 'pages' / 'research.html')
    # The pitches are already in the ratings table, so the list below it holds everything else.
    rows = '\n'.join(
        f'      <a class="lrow" href="{m["path"]}"><p class="kick">{esc(m["kick"])}</p><div><h3>{esc(m["title"])}</h3><p>{esc(m["dek"])}</p></div><p class="tp">{esc(m["topic"])}</p></a>'
        for m, _ in research if m.get('kind') != 'pitch')
    content = (content.replace('{{RESEARCH_ROWS}}', rows)
               .replace('{{PITCH_TABLE}}', pitch_table(research)))
    built.append(write('/research/', page(meta, content, 'research')))

    # Method, About, 404
    for name, nav, body_class in (('method', 'research', 'method'), ('about', 'about', ''), ('404', '', 'page-404')):
        meta, content = read_doc(SRC / 'content' / 'pages' / f'{name}.html')
        target = '/404.html' if name == '404' else meta['path']
        text = page(meta, content, nav, body_class=body_class)
        if name == '404':
            built.append(write_file('/404.html', text))
        else:
            built.append(write(target, text))

    # sitemap.xml, robots.txt, .nojekyll
    today = datetime.date.today().isoformat()
    urls = ['/', '/research/', '/research/method/', '/about/'] + [m['path'] for m, _ in thoughts + research]
    lastmod = {m['path']: m['date'] for m, _ in thoughts + research}
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
