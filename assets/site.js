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

  // ---------- Keep drawn pieces sized to their boxes ----------
  const resize = () => segs.forEach(segInd);
  requestAnimationFrame(resize);
  if ('ResizeObserver' in window) {
    const ro = new ResizeObserver(resize);
    segs.forEach(el => ro.observe(el));
  } else addEventListener('resize', resize);
}
