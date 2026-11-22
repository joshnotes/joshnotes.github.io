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
  const watch = root => { for (const el of $$('.chartbox, .inviz', root)) { if (io) io.observe(el); else el.classList.add('in'); } };
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

  // ---------- Method page: five steps, each with its chart ----------
  const stepsEl = $('#steps');
  if (stepsEl) {
    const hrow = (label, l, w, v, j, extra = '', quiet = false) => `<div class="hb"><span>${label}</span><span class="tr"><i class="b${quiet ? ' q' : ''}" style="--l:${l}%;--w:${w}%;--j:${j}"></i>${extra}</span><span class="v">${v}</span></div>`;
    const ff = {min: 50, max: 120, price: 76, rows: [['52-week range', 62, 88], ['Trading comps', 70, 95], ['Precedent deals', 78, 104], ['DCF, base case', 84, 112], ['Analyst targets', 80, 100]]};
    const pos = v => (v - ff.min) / (ff.max - ff.min) * 100;
    const sc = [['Bear, 25%', 60, 0.25], ['Base, 50%', 94, 0.5], ['Bull, 25%', 120, 0.25]];
    const weighted = sc.reduce((t, [, v, p]) => t + v * p, 0);
    const viz = [
      () => `<p class="fh">Market share</p>` + [['Leader', 28], ['Second', 19], ['Third', 14], ['Rest of market', 39]].map(([l, v], j) => hrow(l, 0, v / 40 * 100, v + '%', j, '', j === 3)).join(''),
      () => `<p class="fh">Revenue by segment</p><div class="mix"><i class="sg" style="flex:46;--j:0"></i><i class="sg s2" style="flex:32;--j:1"></i><i class="sg s3" style="flex:22;--j:2"></i></div><div class="legend"><span><b>46%</b>Products</span><span><b>32%</b>Services</span><span><b>22%</b>Software</span></div>`,
      () => `<p class="fh">How the statements link</p><div class="chain"><span class="box">Income statement</span><span class="arr"></span><span class="box">Cash flow</span><span class="arr"></span><span class="box">Balance sheet</span></div><ul class="checks"><li>Net income flows into cash flow and retained earnings</li><li>Ending cash ties to the balance sheet</li><li>Assets equal liabilities plus equity, every year</li></ul>`,
      () => `<p class="fh">Valuation summary, dollars per share</p>` + ff.rows.map(([l, a, b], j) => hrow(l, pos(a).toFixed(2), (pos(b) - pos(a)).toFixed(2), `$${a} to $${b}`, j, `<i class="px" style="--p:${pos(ff.price).toFixed(2)}%"></i>`, !l.startsWith('DCF'))).join('') +
        `<div class="axis"><span></span><span class="tk">${[50, 70, 90, 110].map(t => `<span style="left:${pos(t).toFixed(2)}%">$${t}</span>`).join('')}</span><span></span></div><p class="fnote">Dashed line: current price, $${ff.price}.</p>`,
      () => `<p class="fh">Scenario values per share</p>` + sc.map(([l, v], j) => hrow(l, 0, v / 130 * 100, '$' + v, j, '', !l.startsWith('Base'))).join('') +
        `<p class="fnote">Probability-weighted value <b>$${weighted.toFixed(0)}</b>, ${Math.round((weighted / ff.price - 1) * 100)}% above the $${ff.price} price.</p>`
    ];
    const stepsTxt = [
      ['Map the industry', 'Who sells what to whom, how big the market is, how fast it grows, and where the profit pools sit.'],
      ['Understand the business', 'Segments, unit economics, customers, and the few numbers that actually drive results.'],
      ['Build the model', 'A three-statement model from the filings, with drivers I can defend line by line.'],
      ['Value it three ways', 'Trading comps, precedent transactions and a DCF, cross-checked against where the stock trades.'],
      ['Write the risks first', 'What would make me wrong, how likely it is, and what it would cost. Bear, base and bull cases.']
    ];
    stepsEl.innerHTML = stepsTxt.map(([h, p], i) => `<article class="st${i ? '' : ' on'}" data-i="${i}"><p class="kick">Step ${i + 1} of 5</p><h3>${h}</h3><p>${p}</p><div class="inviz">${viz[i]()}</div></article>`).join('');
    watch(stepsEl);
  }

  // ---------- Keep drawn pieces sized to their boxes ----------
  const resize = () => { drawDC(); segs.forEach(segInd); };
  requestAnimationFrame(resize);
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(resize);
    [dFig, ...segs].filter(Boolean).forEach(el => ro.observe(el));
  } else addEventListener('resize', resize);
}
