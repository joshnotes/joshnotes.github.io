#!/usr/bin/env python3
"""Draw the link-preview images that LinkedIn, iMessage and others show when a page is shared.

Run after changing content:  python3 src/og.py && python3 src/build.py
Needs Pillow, fontTools and brotli:  pip install pillow fonttools brotli
Each page gets assets/og/<key>.png at 1200 x 627, where the key comes from its path:
/ -> home, /research/ -> research, /research/eaton/ -> research-eaton.
build.py adds the og:image tags for every page that has an image.
"""
import pathlib
import re
import sys
import tempfile

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import MAP_LAYOUTS, ROOT, SRC, load_articles, map_geometry, nice_date, read_doc  # noqa: E402

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


def wordmark(d, x, y, text='joshnotes', size=27, fill=BLACK):
    tracked(d, x, y, text + '.', sans(size, 500), fill, -0.01)


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


def photo_panel(im, path, x0, y0=0, w=None, h=H, focus=(0.5, 0.5)):
    """Paste a photo, in black and white like on the site, cropped to fill the panel."""
    if not path.exists():
        return False
    w = w or W - x0
    ph = ImageOps.grayscale(Image.open(path)).convert('RGB')
    ph = ImageOps.fit(ph, (w * S, h * S), Image.LANCZOS, centering=focus)
    im.paste(ph, (x0 * S, y0 * S))
    return True


def article_image(meta, body):
    im, d = canvas()
    section = 'Notes' if meta['section'] == 'notes' else 'Research'
    figs = key_figures(body) if meta.get('kind') == 'pitch' else []
    photo = ROOT / 'assets' / 'img' / 'lead' / f'{key_for(meta["path"])}-1200.webp'
    panel = 400 if (figs or photo.exists()) else 0
    right_edge = W - panel - M + (0 if not panel else 16)
    wordmark(d, M, M - 8)
    if not panel:
        fm = mono(16)
        tracked(d, W - M - tracked_width(section.upper(), fm), M - 4, section.upper(), fm, BLACK)
    title_block(d, meta['title'], None, M, 168, (W - panel - 2 * M) if panel else W - 2 * M,
                sizes=(60, 54, 50, 46, 42) if panel else (64, 58, 52, 48, 44), max_lines=4 if panel else 3)
    label = meta['kick'] if meta['kick'] == meta['topic'] else f'{meta["kick"]} / {meta["topic"]}'
    footer_labels(d, label, nice_date(meta['date']), right_edge if not panel else W - panel - 56)
    if panel and not figs:
        photo_panel(im, photo, W - panel)
    elif panel:
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


def text_at(d, x, y, anchor, text, font, fill, track=0.0):
    """Text placed by its baseline, anchored start, middle or end, as SVG does it."""
    w = tracked_width(text, font, track)
    x -= {'start': 0, 'middle': w / 2, 'end': w}[anchor]
    x, y = x * S, y * S
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor='ls')
        x += font.getlength(ch) + track * font.size


def draw_map(d, watch, x0, y0, scale):
    """The home page's map, light on black, from the same geometry as the page."""
    lay = MAP_LAYOUTS['tall']
    g = map_geometry(watch, lay)
    F = lay['font']
    P = lambda x, y: ((x0 + x * scale) * S, (y0 + y * scale) * S)  # noqa: E731
    rule, quiet = (74, 70, 66), INK2_DARK
    for x1, y1, x2, y2 in g['spokes']:
        d.line([P(x1, y1), P(x2, y2)], fill=rule, width=2)
    for ln in g['links']:
        x1, y1, x2, y2 = ln['line']
        d.line([P(x1, y1), P(x2, y2)], fill=BONE, width=3)

    def dot(x, y, r, filled):
        (cx, cy), rr = P(x, y), r * scale * S
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=BONE if filled else BLACK, outline=BONE if filled else quiet, width=3)

    def label(lab, font, fill, track=0.0):
        tx, ty, anchor, text = lab
        text_at(d, x0 + tx * scale, y0 + ty * scale, anchor, text, font, fill, track)

    tk, tk_mono, sec_mono = sans(F * scale, 500), mono((F - 2) * scale), mono((F - 1) * scale)
    for c in g['companies']:
        dot(c['x'], c['y'], 4.5, c['piece'])
        label(c['label'], tk, BONE if c['piece'] else quiet)
    for ln in g['links']:
        (cx, cy), rr = P(ln['x'], ln['y']), 9 * scale * S
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=BLACK)
        dot(ln['x'], ln['y'], 5.5 if ln['ticker'] else 4.5, ln['piece'])
        label(ln['label'], tk if ln['ticker'] else tk_mono, BONE if ln['ticker'] else quiet, 0 if ln['ticker'] else 0.06)
    for s in g['sectors']:
        (cx, cy), h = P(s['x'], s['y']), 7 * scale * S
        d.rectangle([cx - h, cy - h, cx + h, cy + h], fill=BONE)
        label(s['label'], sec_mono, BONE, 0.06)


def home_image(meta):
    """Home: the site's one line on bone, and the map of what I follow on black."""
    im, d = canvas()
    panel = 520
    wordmark(d, M, M - 8)
    title_block(d, 'A place to stash my work and thoughts as they come.', None, M, 168, W - panel - 2 * M,
                sizes=(64, 58, 52), max_lines=3)
    x0 = W - panel
    d.rectangle([x0 * S, 0, W * S, H * S], fill=BLACK)
    lay = MAP_LAYOUTS['tall']
    scale = min((panel - 80) / lay['w'], (H - 80) / lay['h'])
    draw_map(d, meta['watchlist'], x0 + (panel - lay['w'] * scale) / 2, (H - lay['h'] * scale) / 2, scale)
    return im


def page_image(title, sub, label, panel_rows=None, photo=None):
    im, d = canvas()
    panel = 440 if (panel_rows or photo) else 0
    wordmark(d, M, M - 8)
    width = W - panel - 2 * M
    title_block(d, title, sub, M, 168, width, sizes=(72, 64, 56), max_lines=2)
    footer_labels(d, label, None)
    if photo:
        photo_panel(im, photo, W - panel, focus=(0.5, 0.35))
    elif panel_rows:
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


def serif_italic(size):
    return ImageFont.truetype(font_file('instrument-serif-latin-400-italic'), size * S)


def wisdom_image():
    """daily dose of wisdom: the name in the page's serif on midnight, and the wheel with its light."""
    import math
    NIGHT, STAR, MIST, LAMP = (0, 0, 0), (233, 228, 218), (162, 157, 151), (243, 181, 98)
    im = Image.new('RGB', (W * S, H * S), NIGHT)
    # Warm glow behind the wheel, drawn soft.
    glow = Image.new('RGB', (W * S, H * S), NIGHT)
    g = ImageDraw.Draw(glow)
    cx, cy, R = 885, 313, 214
    g.ellipse([(cx - 260) * S, (cy - 260) * S, (cx + 260) * S, (cy + 260) * S], fill=(40, 32, 26))
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(120 * S)), 1.0)
    d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate([(130, 520), (520, 90), (610, 560), (1150, 70), (700, 300), (60, 300), (1160, 590), (400, 420)]):
        r = (1.6 if i % 3 else 2.2) * S
        d.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=(235, 230, 220))
    tracked(d, M, M - 8, 'JOSHUVA JOHNSON_', sans(24, 400), STAR, 0.04)
    f = serif_italic(92)
    for k, line in enumerate(['daily dose', 'of wisdom']):
        d.text((M * S, (196 + k * 96) * S), line, font=f, fill=STAR)
    d.text((M * S, 432 * S), 'Spin for a random episode', font=sans(24), fill=MIST)
    d.text((M * S, 466 * S), 'from seven podcasts.', font=sans(24), fill=MIST)
    # Orbit, then the light running round it (a soft copy underneath for the glow).
    d.ellipse([(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S], outline=(42, 40, 37), width=2)
    arc = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    a = ImageDraw.Draw(arc)
    box = [(cx - R) * S, (cy - R) * S, (cx + R) * S, (cy + R) * S]
    for k in range(24):  # tail fades toward the back
        start = 146 + k * 3  # head ends on the lit tile at about 219 degrees
        a.arc(box, start, start + 3.4, fill=LAMP + (int(30 + 225 * k / 23),), width=5 * S // 2)
    soft = arc.filter(ImageFilter.GaussianBlur(7 * S))
    im.paste(soft, (0, 0), soft)
    im.paste(arc, (0, 0), arc)
    d = ImageDraw.Draw(im)
    # Seven tiles evenly round the orbit; the one under the light is lit.
    for i in range(7):
        ang = math.radians(-90 + i * 360 / 7)
        x, y, h = cx + R * math.cos(ang), cy + R * math.sin(ang), 30
        lit = i == 6
        if lit:
            halo = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
            ImageDraw.Draw(halo).rounded_rectangle([(x - h - 10) * S, (y - h - 10) * S, (x + h + 10) * S, (y + h + 10) * S], 18 * S, fill=LAMP + (150,))
            halo = halo.filter(ImageFilter.GaussianBlur(14 * S))
            im.paste(halo, (0, 0), halo)
            d = ImageDraw.Draw(im)
        d.rounded_rectangle([(x - h) * S, (y - h) * S, (x + h) * S, (y + h) * S], 12 * S,
                            fill=(26, 25, 23) if not lit else (58, 52, 40), outline=LAMP if lit else (66, 63, 58), width=3 if lit else 2)
    # The hub and its lamp-light ring.
    hr = 128
    d.ellipse([(cx - hr) * S, (cy - hr) * S, (cx + hr) * S, (cy + hr) * S], fill=(14, 13, 12), outline=(40, 38, 35), width=2)
    rr = 102
    ring = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline=LAMP + (255,), width=3)
    glow_ring = ring.filter(ImageFilter.GaussianBlur(6 * S))
    im.paste(glow_ring, (0, 0), glow_ring)
    im.paste(ring, (0, 0), ring)
    d = ImageDraw.Draw(im)
    fm = mono(12, 500)
    tracked(d, cx - tracked_width('GET MY', fm, 0.18) / 2, cy - 44, 'GET MY', fm, LAMP, 0.18)
    fs = serif_italic(30)
    for k, line in enumerate(['daily dose', 'of wisdom']):
        w = fs.getlength(line) / S
        d.text(((cx - w / 2) * S, (cy - 22 + k * 32) * S), line, font=fs, fill=STAR)
    return im


def main():
    made = []
    notes, research = load_articles('notes'), load_articles('research')
    for meta, body in notes + research:
        made.append(save(article_image(meta, body), key_for(meta['path'])))
    made.append(save(home_image(read_doc(SRC / 'content' / 'pages' / 'home.html')[0]), 'home'))
    rows = []
    for meta, body in research:
        figs = key_figures(body) if meta.get('kind') == 'pitch' else []
        if len(figs) >= 3:
            rows.append((meta['title'].split(':')[0].split(' after ')[0], figs[0][0], figs[2][0]))
    portrait = ROOT / 'assets' / 'img' / 'joshuva-johnson-1440.jpg'
    pages = {'research': ('Research', None, 'Research', rows[:3], None),
             'research-method': ('Pitch Framework', 'Five steps, from the industry down to one value per share.', 'Research / Pitch Framework', None, None),
             'about': ('Joshuva Johnson', 'Analyst, JPMorgan Chase, New York', 'About', None, portrait)}
    for key, (title, sub, label, panel_rows, photo) in pages.items():
        made.append(save(page_image(title, sub, label, panel_rows, photo), key))
    made.append(save(wisdom_image(), 'wisdom'))
    for p in made:
        print('drew', p.relative_to(ROOT))


if __name__ == '__main__':
    main()
