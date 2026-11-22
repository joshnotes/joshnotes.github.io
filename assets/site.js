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

  // ---------- Discount-rate calculator: value of a growing perpetuity, 1 / (r - g) ----------
  const dFig = $('#dc-fig'), dIn = $('#dc-r');
  let drawDC = () => {};
  if (dFig && dIn) {
    const g = 0.03, r0 = 0.06, r1 = 0.12;
    let rate = 0.095, dGeom = null;
    const val = r => 1 / (r - g);
    const pct = r => (r * 100).toFixed(1) + '%';
    const dPad = {l: 6, r: 6, t: 14, b: 28};
    const placeDC = () => {
      if (!dGeom) return;
      const gx = $('#dc-x'), gp = $('#dc-p'); if (!gx) return;
      const x = dGeom.X(rate).toFixed(1), y = dGeom.Y(val(rate)).toFixed(1);
      gx.style.transform = `translate(${x}px,0)`;
      gp.style.transform = `translate(${x}px,${y}px)`;
    };
    drawDC = () => {
      const W = dFig.clientWidth, H = dFig.clientHeight; if (!W) return;
      const X = r => dPad.l + (r - r0) / (r1 - r0) * (W - dPad.l - dPad.r);
      const yMax = val(r0) * 1.04;
      const Y = v => dPad.t + (1 - v / yMax) * (H - dPad.t - dPad.b);
      dGeom = {X, Y};
      let d = '';
      for (let i = 0; i <= 120; i++) { const r = r0 + (r1 - r0) * i / 120; d += (i ? 'L' : 'M') + X(r).toFixed(1) + ' ' + Y(val(r)).toFixed(1); }
      const x = X(rate).toFixed(1), y = Y(val(rate)).toFixed(1);
      const ticks = [0.06, 0.08, 0.10, 0.12].filter((t, i) => W > 360 || i % 2 === 0);
      dFig.innerHTML = `<svg aria-hidden="true"><defs><linearGradient id="dcg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="currentColor" stop-opacity=".22"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></linearGradient></defs>
        <path d="${d} L${X(r1).toFixed(1)} ${H - dPad.b} L${X(r0).toFixed(1)} ${H - dPad.b}Z" fill="url(#dcg)"/>
        <path class="ln" pathLength="1" d="${d}"/>
        ${ticks.map(t => `<text class="tick" x="${X(t).toFixed(1)}" y="${H - 6}" text-anchor="${t === r0 ? 'start' : t === r1 ? 'end' : 'middle'}">${Math.round(t * 100)}%</text>`).join('')}
        <g id="dc-x" class="mv" style="transform:translate(${x}px,0)"><line class="xh" x1="0" x2="0" y1="${dPad.t}" y2="${H - dPad.b}"/></g>
        <g id="dc-p" class="mv" style="transform:translate(${x}px,${y}px)"><circle class="halo" r="14"/><circle class="dot" r="6"/></g></svg>`;
    };
    const setRate = r => {
      rate = Math.min(r1, Math.max(r0, Math.round(r * 1000) / 1000));
      $('#dc-out').textContent = '$' + val(rate).toFixed(2);
      $('#dc-cap').textContent = `Value today of $1 of cash flow next year, growing 3% a year forever, at a ${pct(rate)} discount rate.`;
      $('#dc-v').textContent = pct(rate);
      $('#dc-delta').textContent = `One point higher, at ${pct(rate + 0.01)}, cuts the value by ${Math.round((1 - val(rate + 0.01) / val(rate)) * 100)}%.`;
      dIn.value = (rate * 100).toFixed(1);
      dIn.setAttribute('aria-valuetext', `${pct(rate)}, value $${val(rate).toFixed(2)}`);
      placeDC();
    };
    const scrubDC = e => { const b = dFig.getBoundingClientRect(); setRate(r0 + (e.clientX - b.left - dPad.l) / (b.width - dPad.l - dPad.r) * (r1 - r0)); };
    dFig.addEventListener('pointermove', scrubDC);
    dFig.addEventListener('pointerdown', scrubDC);
    dIn.addEventListener('input', () => setRate(+dIn.value / 100));
    drawDC();
    setRate(0.095);
  }

  // ---------- Keep drawn pieces sized to their boxes ----------
  const resize = () => { drawDC(); segs.forEach(segInd); };
  requestAnimationFrame(resize);
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(resize);
    [dFig, ...segs].filter(Boolean).forEach(el => ro.observe(el));
  } else addEventListener('resize', resize);
}
