#!/usr/bin/env python3
"""Draw the link-preview images that LinkedIn, iMessage and others show when a page is shared.

Run after changing content:  python3 src/og.py && python3 src/build.py
Needs Pillow, fontTools and brotli:  pip install pillow fonttools brotli
Each page gets assets/og/<key>.png at 1200 x 627, where the key comes from its path:
/ -> home, /research/ -> research, /research/eaton/ -> research-eaton.
build.py adds the og:image tags for every page that has an image.
"""
import math
import pathlib
import re
import sys
import tempfile

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import ROOT, load_articles, nice_date  # noqa: E402

W, H, S = 1200, 627, 2          # final size, drawn at 2x and scaled down
M = 72                          # outer margin
BONE, BLACK = (227, 222, 217), (0, 0, 0)
INK2, INK2_DARK, DIM_DARK = (85, 81, 76), (162, 157, 151), (110, 105, 99)
OUT = ROOT / 'assets' / 'og'

_tmp = pathlib.Path(tempfile.mkdtemp())
_ttf = {}


def font_file(name):
    """The site serves woff2; Pillow wants TrueType, so convert once per run."""
    if name not in _ttf:
        f = TTFont(ROOT / 'assets' / 'fonts' / f'{name}.woff2')
        f.flavor = None
        _ttf[name] = _tmp / f'{name}.ttf'
        f.save(_ttf[name])
    return str(_ttf[name])


def sans(size, weight=400):
    f = ImageFont.truetype(font_file('geist-latin-wght-normal'), size * S)
    f.set_variation_by_axes([weight])
    return f


def mono(size, weight=400):
    f = ImageFont.truetype(font_file('geist-mono-latin-wght-normal'), size * S)
    f.set_variation_by_axes([weight])
    return f


def key_for(path):
    return path.strip('/').replace('/', '-') or 'home'


def tracked(d, x, y, text, font, fill, track=0.06):
    """Draw text with letter-spacing (in em), the way the site sets mono labels. Returns the end x."""
    x, y = x * S, y * S
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + track * font.size
    return x / S


def tracked_width(text, font, track=0.06):
    return (sum(font.getlength(ch) for ch in text) + track * font.size * len(text)) / S


def wrap(text, font, width):
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if font.getlength(trial) / S <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def fit(text, width, max_lines, sizes, weight=300):
    """Largest size at which the text fits in max_lines."""
    for size in sizes:
        f = sans(size, weight)
        lines = wrap(text, f, width)
        if len(lines) <= max_lines:
            return f, size, lines
    return f, size, lines[:max_lines]


def canvas():
    im = Image.new('RGB', (W * S, H * S), BONE)
    return im, ImageDraw.Draw(im)


def bar(d, x, y, fill=BLACK):
    d.rectangle([x * S, y * S, (x + 120) * S, (y + 8) * S], fill=fill)


def wordmark(d, x, y, text='Joshuva Johnson', size=24, fill=BLACK):
    tracked(d, x, y, text.upper() + '_', sans(size, 400), fill, 0.04)


def save(im, key):
    OUT.mkdir(parents=True, exist_ok=True)
    im.resize((W, H), Image.LANCZOS).save(OUT / f'{key}.png', optimize=True)
    return OUT / f'{key}.png'


def title_block(d, title, sub, x, y, width, sizes=(64, 58, 52, 48, 44), max_lines=3, sub_size=24):
    f, size, lines = fit(title, width, max_lines, sizes)
    lh = round(size * 1.1)
    for i, ln in enumerate(lines):
        d.text((x * S, (y + i * lh) * S), ln, font=f, fill=BLACK)
    y += len(lines) * lh + 30
    bar(d, x, y)
    y += 8 + 30
    if sub:
        fs = sans(sub_size, 400)
        for i, ln in enumerate(wrap(sub, fs, width)[:3]):
            d.text((x * S, (y + i * round(sub_size * 1.45)) * S), ln, font=fs, fill=INK2)
    return y


def footer_labels(d, left, right, right_edge=W - M, fill=INK2):
    fm = mono(16)
    tracked(d, M, H - M - 14, left.upper(), fm, fill)
    if right:
        tracked(d, right_edge - tracked_width(right.upper(), fm), H - M - 14, right.upper(), fm, fill)


def key_figures(body):
    m = re.search(r'<div class="kf[^"]*">(.*?)</div></div>', body, re.S)
    return re.findall(r'<b>(.*?)</b><span>(.*?)</span>', m.group(1)) if m else []


def article_image(meta, body):
    im, d = canvas()
    section = 'Thoughts' if meta['section'] == 'thoughts' else 'Research'
    figs = key_figures(body) if meta.get('kind') == 'pitch' else []
    panel = 400 if figs else 0
    right_edge = W - panel - M + (0 if not panel else 16)
    wordmark(d, M, M - 8)
    if not panel:
        fm = mono(16)
        tracked(d, W - M - tracked_width(section.upper(), fm), M - 4, section.upper(), fm, BLACK)
    title_block(d, meta['title'], None, M, 168, (W - panel - 2 * M) if panel else W - 2 * M,
                sizes=(60, 54, 50, 46, 42) if panel else (64, 58, 52, 48, 44), max_lines=4 if panel else 3)
    footer_labels(d, f'{meta["kick"]} / {meta["topic"]}', nice_date(meta['date']), right_edge if not panel else W - panel - 56)
    if panel:
        x0 = W - panel
        d.rectangle([x0 * S, 0, W * S, H * S], fill=BLACK)
        labels = ['Rating', 'Value per share', 'Value vs price', figs[3][1].replace(', 2026', '').replace('Price at', 'Price,')]
        y = M - 6
        for (val, _), label in zip(figs[:4], labels):
            fv = sans(48, 300)
            d.text(((x0 + 48) * S, y * S), val, font=fv, fill=BONE)
            tracked(d, x0 + 48, y + 60, label.upper(), mono(14), INK2_DARK)
            y += 122
    return im


def pv(rate, t, g=0.03):
    return (1 + g) ** (t - 1) / (1 + rate) ** t


def home_image(meta):
    im, d = canvas()
    half = W // 2
    d.rectangle([half * S, 0, W * S, H * S], fill=BLACK)
    # Left: the name of the publication, the line, the author.
    f = sans(44, 400)
    tracked(d, M, 210, 'THOUGHTSBYJOSH_', f, BLACK, 0.03)
    d.text((M * S, 286 * S), 'Hot takes, discounted', font=sans(26, 400), fill=BLACK)
    d.text((M * S, 322 * S), 'to present value.', font=sans(26, 400), fill=BLACK)
    d.text((M * S, 384 * S), 'By Joshuva Johnson', font=sans(20, 400), fill=INK2)
    footer_labels(d, 'Markets and stock pitches', None)
    # Right: one line per year, sized by what $1 growing 3% is worth today at 9.5%.
    g, r, r0, years = 0.03, 0.095, 0.06, 60
    x0, x1, yb, top = half + 56, W - 56, H - 120, 230
    tracked(d, x0, 72, 'WHAT A DISCOUNT RATE DOES TO VALUE', mono(13), INK2_DARK)
    d.text((x0 * S, 102 * S), f'${1 / (r - g):.2f}', font=sans(64, 300), fill=BONE)
    half_year = math.log(0.5) / math.log((1 + g) / (1 + r))
    step = (x1 - x0) / years
    for t in range(1, years + 1):
        x = x0 + (t - 0.5) * step
        y = yb - pv(r, t) / pv(r0, 1) * (yb - top)
        d.line([(x * S, y * S), (x * S, yb * S)], fill=BONE if t <= half_year else DIM_DARK, width=3)
    d.line([(x0 * S, (yb + 1) * S), (x1 * S, (yb + 1) * S)], fill=(46, 43, 40), width=2)
    tracked(d, x0, yb + 18, 'YEAR 1', mono(12), INK2_DARK)
    tracked(d, x1 - tracked_width('60', mono(12)), yb + 18, '60', mono(12), INK2_DARK)
    d.text((x0 * S, (yb + 50) * S), f'At a 9.5% discount rate, half the value comes after year {round(half_year)}.', font=sans(15, 400), fill=INK2_DARK)
    wordmark(d, M, M - 8, size=20)
    return im


def page_image(title, sub, label, panel_rows=None):
    im, d = canvas()
    panel = 440 if panel_rows else 0
    wordmark(d, M, M - 8)
    width = W - panel - 2 * M
    title_block(d, title, sub, M, 168, width, sizes=(72, 64, 56), max_lines=2)
    footer_labels(d, label, None)
    if panel_rows:
        x0 = W - panel
        d.rectangle([x0 * S, 0, W * S, H * S], fill=BLACK)
        tracked(d, x0 + 48, M - 4, 'STOCK PITCHES', mono(14), INK2_DARK)
        y = M + 40
        for company, rating, gap in panel_rows:
            d.line([((x0 + 48) * S, y * S), ((W - 48) * S, y * S)], fill=(46, 43, 40), width=2)
            d.text(((x0 + 48) * S, (y + 22) * S), company, font=sans(30, 300), fill=BONE)
            d.text(((x0 + 48) * S, (y + 64) * S), f'{rating}, value {gap} vs price', font=sans(17, 400), fill=INK2_DARK)
            y += 116
    return im


def main():
    made = []
    thoughts, research = load_articles('thoughts'), load_articles('research')
    for meta, body in thoughts + research:
        made.append(save(article_image(meta, body), key_for(meta['path'])))
    made.append(save(home_image(None), 'home'))
    rows = []
    for meta, body in research:
        figs = key_figures(body) if meta.get('kind') == 'pitch' else []
        if len(figs) >= 3:
            rows.append((meta['title'].split(':')[0].split(' after ')[0], figs[0][0], figs[2][0]))
    pages = {'research': ('Research', 'Stock pitches, deal breakdowns and industry notes, built from public filings.', 'Research', rows[:3]),
             'research-method': ('How I build a pitch', 'Five steps, from the industry down to one value per share.', 'Research / Method', None),
             'about': ('Joshuva Johnson', 'Analyst at JPMorgan Chase in New York. I write about markets, companies and deals.', 'About', None)}
    for key, (title, sub, label, panel_rows) in pages.items():
        made.append(save(page_image(title, sub, label, panel_rows), key))
    for p in made:
        print('drew', p.relative_to(ROOT))


if __name__ == '__main__':
    main()
