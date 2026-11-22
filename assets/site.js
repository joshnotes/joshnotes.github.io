// Shared behaviour for every page. Each block runs only if its markup is on the page.
{
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const hasIO = 'IntersectionObserver' in window;
  const reduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  const animate = hasIO && !reduce;
  const rootEl = document.documentElement;
  if (hasIO) rootEl.classList.add('io');
  if (animate) rootEl.classList.add('js');

  // ---------- Exhibit bars grow once, the first time they scroll into view ----------
  const io = animate ? new IntersectionObserver(entries => {
    for (const e of entries) { if (!e.isIntersecting) continue; e.target.classList.add('in'); io.unobserve(e.target); }
  }, {rootMargin: '0px 0px -10% 0px', threshold: 0}) : null;
  const watch = root => { for (const el of $$('.chartbox', root)) { if (io) io.observe(el); else el.classList.add('in'); } };
  watch(document);

  // ---------- Segmented filters (buttons are in the HTML; items carry data-k) ----------
  const segs = $$('.segc[data-filter]');
  const segInd = seg => {
    const ind = $('.ind', seg), b = $('button[aria-pressed=true]', seg);
    if (!ind || !b || !b.offsetWidth) return;
    ind.style.width = b.offsetWidth + 'px';
    ind.style.transform = `translateX(${b.offsetLeft}px)`;
  };
  for (const seg of segs) {
    const target = document.getElementById(seg.dataset.filter);
    if (!target) continue;
    seg.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      for (const x of $$('button', seg)) x.setAttribute('aria-pressed', String(x === b));
      segInd(seg);
      const k = b.dataset.k;
      for (const item of target.children) item.hidden = !!k && item.dataset.k !== k;
    });
  }

  // ---------- Discount-rate figure: value of a growing perpetuity, 1 / (r - g) ----------
  // One line per year. Line t is what year t's cash flow, $1 growing 3% a year, is worth today.
  // The lines add up to the big number; dimmed lines are the years after half the value is reached.
  const dFig = $('#dc-fig'), dIn = $('#dc-r');
  let drawDC = () => {};
  if (dFig && dIn) {
    const g = 0.03, r0 = 0.06, r1 = 0.12, YEARS = 60;
    let rate = 0.095;
    const val = r => 1 / (r - g);
    const pv = (r, t) => Math.pow(1 + g, t - 1) / Math.pow(1 + r, t);
    const half = r => Math.log(0.5) / Math.log((1 + g) / (1 + r));
    const pct = r => (r * 100).toFixed(1) + '%';
    const pad = {t: 4, b: 24};
    let lines = [];
    const place = () => {
      const H = dFig.clientHeight, top = pv(r0, 1), h = half(rate);
      lines.forEach((ln, i) => {
        const t = i + 1, y = pad.t + (1 - pv(rate, t) / top) * (H - pad.t - pad.b);
        ln.setAttribute('y1', y.toFixed(1));
        ln.classList.toggle('late', t > h);
      });
    };
    drawDC = () => {
      const W = dFig.clientWidth, H = dFig.clientHeight; if (!W) return;
      const step = W / YEARS, x = t => (t - 0.5) * step, yB = H - pad.b;
      let svg = `<svg aria-hidden="true"><line class="base" x1="0" x2="${W}" y1="${yB + 0.5}" y2="${yB + 0.5}"/>`;
      for (let t = 1; t <= YEARS; t++) svg += `<line class="yr" style="--d:${(t * 9)}ms" x1="${x(t).toFixed(1)}" x2="${x(t).toFixed(1)}" y1="${yB}" y2="${yB}"/>`;
      svg += [1, 20, 40, 60].map(t => `<text class="tick" x="${t === 1 ? 0 : t === YEARS ? W : x(t).toFixed(1)}" y="${H - 4}" text-anchor="${t === 1 ? 'start' : t === YEARS ? 'end' : 'middle'}">${t === 1 ? 'YEAR 1' : t}</text>`).join('') + '</svg>';
      dFig.innerHTML = svg;
      lines = $$('.yr', dFig);
      place();
    };
    const setRate = r => {
      rate = Math.min(r1, Math.max(r0, Math.round(r * 1000) / 1000));
      $('#dc-out').textContent = '$' + val(rate).toFixed(2);
      $('#dc-cap').textContent = `Value today of $1 of cash flow next year, growing 3% a year forever, at a ${pct(rate)} discount rate.`;
      $('#dc-v').textContent = pct(rate);
      $('#dc-delta').textContent = `Half of that value comes after year ${Math.round(half(rate))}. One point higher, at ${pct(rate + 0.01)}, cuts the value by ${Math.round((1 - val(rate + 0.01) / val(rate)) * 100)}%.`;
      dIn.value = (rate * 100).toFixed(1);
      dIn.setAttribute('aria-valuetext', `${pct(rate)}, value $${val(rate).toFixed(2)}`);
      place();
    };
    dIn.addEventListener('input', () => setRate(+dIn.value / 100));
    drawDC();
    setRate(0.095);
    if (animate) requestAnimationFrame(() => requestAnimationFrame(() => dFig.classList.add('in')));
  }

  // ---------- Keep drawn pieces sized to their boxes ----------
  const resize = () => { drawDC(); segs.forEach(segInd); };
  requestAnimationFrame(resize);
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(resize);
    [dFig, ...segs].filter(Boolean).forEach(el => ro.observe(el));
  } else addEventListener('resize', resize);
}
