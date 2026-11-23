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

  // ---------- Photos: black and white until hovered; on touch screens a tap turns colour on and off ----------
  for (const fig of $$('.photo')) fig.addEventListener('click', e => { if (!e.target.closest('a')) fig.classList.toggle('on'); });

  // ---------- Home map: point at, focus or tap a sector (or a link) to light up what it connects ----------
  // Pointing or keyboard focus previews; a click or tap pins it until the next click, tap or Escape.
  for (const wm of $$('.wm')) {
    let pinned = '', peek = '';
    const show = () => {
      const k = peek || pinned;
      if (k) wm.dataset.on = k; else delete wm.dataset.on;
      for (const b of $$('[role=button][data-k]', wm)) b.setAttribute('aria-pressed', String(b.dataset.k === pinned));
    };
    const keyAt = el => (el && el.closest ? el.closest('[data-k]') : null);
    wm.addEventListener('pointerover', e => { if (e.pointerType === 'mouse') { const t = keyAt(e.target); peek = t ? t.dataset.k : ''; show(); } });
    wm.addEventListener('pointerleave', () => { peek = ''; show(); });
    wm.addEventListener('focusin', e => { const t = keyAt(e.target); if (t && t.matches(':focus-visible')) { peek = t.dataset.k; show(); } });
    wm.addEventListener('focusout', () => { peek = ''; show(); });
    const pin = k => { pinned = pinned === k ? '' : k; show(); };
    wm.addEventListener('click', e => {
      const t = keyAt(e.target);
      if (!t || t.closest('a')) return; // filled dots are links: let them open the piece
      pin(t.dataset.k);
    });
    wm.addEventListener('keydown', e => {
      const t = keyAt(e.target);
      if (e.key === 'Escape') { pinned = ''; show(); }
      else if (t && t.getAttribute('role') === 'button' && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); pin(t.dataset.k); }
    });
    document.addEventListener('click', e => { if (pinned && !wm.contains(e.target)) { pinned = ''; show(); } });
  }

  // ---------- The way into daily dose of wisdom: midnight opens from the click, then the page loads ----------
  document.addEventListener('click', e => {
    const a = e.target.closest && e.target.closest('a[href="/wisdom/"]');
    if (!a || reduce || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (location.pathname === '/wisdom/') return;
    e.preventDefault();
    const o = document.createElement('div');
    o.className = 'portal-out';
    o.style.setProperty('--x', (e.clientX || innerWidth / 2) + 'px');
    o.style.setProperty('--y', (e.clientY || innerHeight / 2) + 'px');
    document.body.appendChild(o);
    setTimeout(() => { location.href = a.href; }, 520);
  });
  // Coming back with the Back button: clear the door so the page isn't left dark.
  addEventListener('pageshow', e => { if (e.persisted) for (const o of $$('.portal-out')) o.remove(); });

  // ---------- Keep drawn pieces sized to their boxes ----------
  const resize = () => segs.forEach(segInd);
  requestAnimationFrame(resize);
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(resize);
    segs.forEach(el => ro.observe(el));
  } else addEventListener('resize', resize);
}
