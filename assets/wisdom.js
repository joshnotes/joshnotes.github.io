// daily dose of wisdom: a light runs round seven podcasts, slows down, and stops on one.
// While it turns, the page asks Apple Podcasts for that show's recent episodes and picks one at random.
(() => {
  const root = document.querySelector('.wz');
  const data = document.getElementById('wz-data');
  if (!root || !data) return;

  const shows = JSON.parse(data.textContent);
  const N = shows.length, STEP = 360 / N;
  const reduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  const $ = s => root.querySelector(s);
  const tiles = [...root.querySelectorAll('.wz-show')];
  const comet = $('.wz-comet'), spinBtn = $('.wz-spin'), ticker = $('.wz-ticker'), hubCover = $('.wz-hub-cover');
  const shock = $('.wz-shock'), stage = $('.wz-stage'), tilt = $('.wz-tilt');
  const card = $('.wz-card'), cover = $('.wz-cover'), showName = $('.wz-show-name'), meta = $('.wz-meta');
  const title = $('.wz-ep'), audio = $('.wz-audio'), again = $('.wz-again'), apple = $('.wz-apple'), live = $('.wz-live');

  const html = document.documentElement;
  const rnd = (a, b) => a + Math.random() * (b - a);

  // ---------- The way in: light spirals into the black hole, timed off the CSS animation of its centre ----------
  const portal = document.querySelector('.wz-portal');
  if (portal) {
    const done = () => { if (portal.isConnected) portal.remove(); };
    if (reduce || !html.classList.contains('portal')) done();
    else {
      const core = portal.querySelector('.bh-core'), cv = portal.querySelector('.wz-infall'), c = cv.getContext && cv.getContext('2d');
      const coreAnim = core.getAnimations ? core.getAnimations()[0] : null;
      const t0 = performance.now();
      const clock = () => (coreAnim && coreAnim.currentTime != null ? coreAnim.currentTime : performance.now() - t0) / 1000;
      let running = !!c;
      if (c) {
        const D = Math.min(1.5, devicePixelRatio || 1), W = innerWidth, H = innerHeight, cx = W / 2, cy = H / 2;
        cv.width = W * D; cv.height = H * D; c.setTransform(D, 0, 0, D, 0, 0);
        const rMax = Math.hypot(W, H) / 2 * 1.05, horizon = Math.min(W, H) * 0.14; // the CSS centre is 28vmin across
        const coreR = t => { // follows the bh-core keyframes closely enough to swallow the light at the rim
          const k = t / 2.4;
          if (k < 0.28) return horizon * Math.sin(k / 0.28 * Math.PI / 2);
          if (k < 0.6) return horizon * (1 + 0.08 * (k - 0.28) / 0.32);
          return horizon * (1.08 + 12.92 * Math.pow(Math.min(1, (k - 0.6) / 0.32), 2.2));
        };
        const tones = ['255,246,230', '255,232,196', '243,181,98', '255,214,160'];
        const n = Math.min(420, Math.round(W * H / 3200));
        const spawn = (p, outer) => {
          p.a = rnd(0, Math.PI * 2); p.r = outer ? rMax * rnd(0.9, 1.1) : rMax * rnd(0.25, 1.1);
          p.w = rnd(0.5, 1.7); p.v = rnd(0.6, 1.4); p.tone = tones[Math.floor(Math.random() * tones.length)]; p.age = 0;
          return p;
        };
        const ps = Array.from({length: n}, () => spawn({}, false));
        let last = clock();
        const frame = () => {
          if (!running) return;
          const t = clock(), dt = Math.min(0.05, Math.max(0, t - last)); last = t;
          c.fillStyle = 'rgba(0,0,0,0.24)'; c.fillRect(0, 0, W, H); // short trails
          const rc = coreR(t);
          c.lineCap = 'round';
          for (const p of ps) {
            if (p.dead) continue;
            const x0 = cx + Math.cos(p.a) * p.r, y0 = cy + Math.sin(p.a) * p.r;
            const pull = (0.35 + 2.6 * Math.pow(rMax / Math.max(p.r, 1), 0.9)) * p.v * (0.6 + t * 0.9);
            p.r -= p.r * pull * dt * 0.55;
            p.a += pull * dt * 0.9; // the closer it gets, the faster it turns
            p.age += dt;
            if (p.r <= rc * 1.02) { if (t < 1.55) spawn(p, true); else p.dead = true; continue; }
            const x1 = cx + Math.cos(p.a) * p.r, y1 = cy + Math.sin(p.a) * p.r;
            const alpha = Math.min(1, p.age * 3) * Math.min(1, 0.25 + 1.4 * (1 - p.r / rMax));
            c.strokeStyle = `rgba(${p.tone},${alpha.toFixed(3)})`; c.lineWidth = p.w;
            c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke();
          }
          if (t < 2.4) requestAnimationFrame(frame); else running = false;
        };
        requestAnimationFrame(frame);
      }
      const skip = () => { running = false; html.classList.add('portal-skip'); done(); };
      portal.addEventListener('pointerdown', skip, {once: true});
      addEventListener('keydown', function k(e) { if (!portal.isConnected) return removeEventListener('keydown', k); if (!e.metaKey && !e.ctrlKey && !e.altKey) skip(); });
      setTimeout(() => { running = false; done(); }, 3000);
    }
  }

  // ---------- The sky: every star keeps its own time, some flare at random, and now and then one falls ----------
  const sky = document.querySelector('.wz-sky');
  const ctx = sky && sky.getContext && sky.getContext('2d');
  if (ctx) {
    const tones = ['255,250,240', '255,238,212', '233,228,218', '255,214,160'];
    let W = 0, H = 0, stars = [], meteors = [], nextMeteor = performance.now() + rnd(2500, 5000), lastDraw = 0;
    const build = () => {
      const D = Math.min(1.5, devicePixelRatio || 1);
      W = innerWidth; H = innerHeight; sky.width = W * D; sky.height = H * D; ctx.setTransform(D, 0, 0, D, 0, 0);
      stars = Array.from({length: Math.min(260, Math.round(W * H / 6500))}, () => ({
        x: Math.random() * W, y: Math.random() * H, r: Math.random() < 0.86 ? rnd(0.35, 0.95) : rnd(1.05, 1.7),
        a: rnd(0.12, 0.6), s: rnd(0.25, 1.4), p: rnd(0, 6.283), c: tones[Math.floor(Math.random() * tones.length)], f: 0, fd: 0}));
    };
    const draw = now => {
      ctx.clearRect(0, 0, W, H);
      for (const s of stars) {
        let k = 0;
        if (!s.f && Math.random() < 0.0009) { s.f = now; s.fd = rnd(700, 1600); } // a random star flares
        if (s.f) { const q = (now - s.f) / s.fd; if (q >= 1) s.f = 0; else k = Math.sin(Math.PI * q); }
        const tw = s.a * (0.55 + 0.45 * Math.sin(now / 1000 * s.s + s.p));
        const al = Math.min(1, tw + k * 0.95), r = s.r * (1 + k * 0.9);
        ctx.fillStyle = `rgba(${s.c},${al.toFixed(3)})`;
        ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, 6.283); ctx.fill();
        if (k > 0.25) { // the glint of a flaring star
          const g = r * 7 * k;
          ctx.strokeStyle = `rgba(${s.c},${(k * 0.55).toFixed(3)})`; ctx.lineWidth = 0.7;
          ctx.beginPath(); ctx.moveTo(s.x - g, s.y); ctx.lineTo(s.x + g, s.y); ctx.moveTo(s.x, s.y - g); ctx.lineTo(s.x, s.y + g); ctx.stroke();
        }
      }
      if (now > nextMeteor) { // a shooting star, from the top half, slanting down either way
        const dir = Math.random() < 0.5 ? -1 : 1, ang = rnd(0.32, 0.62), sp = rnd(800, 1300);
        meteors.push({x: rnd(W * 0.15, W * 0.85), y: rnd(-20, H * 0.35), vx: Math.cos(ang) * sp * dir, vy: Math.sin(ang) * sp, len: rnd(140, 280), t0: now, life: rnd(700, 1100)});
        nextMeteor = now + rnd(2500, 7000);
      }
      meteors = meteors.filter(m => now - m.t0 < m.life);
      for (const m of meteors) {
        const e = (now - m.t0) / 1000, q = (now - m.t0) / m.life, al = Math.sin(Math.PI * q);
        const hx = m.x + m.vx * e, hy = m.y + m.vy * e, sp = Math.hypot(m.vx, m.vy), L = m.len * Math.min(1, q * 3);
        const tx = hx - m.vx / sp * L, ty = hy - m.vy / sp * L;
        const gr = ctx.createLinearGradient(tx, ty, hx, hy);
        gr.addColorStop(0, 'rgba(255,236,205,0)'); gr.addColorStop(1, `rgba(255,246,228,${al.toFixed(3)})`);
        ctx.strokeStyle = gr; ctx.lineWidth = 1.6; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(hx, hy); ctx.stroke();
        ctx.fillStyle = `rgba(255,248,235,${al.toFixed(3)})`; ctx.beginPath(); ctx.arc(hx, hy, 1.6, 0, 6.283); ctx.fill();
      }
    };
    build();
    if (reduce) draw(0); // a still sky
    else {
      const loop = now => {
        // Full rate while a star is falling, half rate otherwise (it only twinkles),
        // and the sky holds still while the wheel spins so the spin gets every frame.
        const busy = root.dataset.state === 'spinning';
        if (busy) nextMeteor = Math.max(nextMeteor, now + 1500);
        if (meteors.length || (!busy && now - lastDraw > 32)) { draw(now); lastDraw = now; }
        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }
    let rt = 0;
    addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { build(); if (reduce) draw(0); }, 150); });
  }

  const art = (s, px) => `${s.art}/${px}x${px}bb.jpg`;
  const rand = n => { const a = new Uint32Array(1); crypto.getRandomValues(a); return a[0] % n; };
  const minutes = ms => {
    const m = Math.max(1, Math.round(ms / 60000));
    return m < 60 ? `${m} min` : `${Math.floor(m / 60)} hr${m % 60 ? ` ${m % 60} min` : ''}`;
  };
  const day = iso => new Date(iso).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'});

  // One request per show per visit: the show's 200 most recent episodes, from Apple's public lookup.
  const cache = new Map();
  const episodes = show => {
    if (cache.has(show.id)) return cache.get(show.id);
    const ctl = 'AbortController' in window ? new AbortController() : null;
    const timer = ctl && setTimeout(() => ctl.abort(), 10000);
    const p = fetch(`https://itunes.apple.com/lookup?id=${show.id}&media=podcast&entity=podcastEpisode&limit=200`, ctl ? {signal: ctl.signal} : {})
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(d => {
        const list = (d.results || []).filter(x => x.wrapperType === 'podcastEpisode' && /^https:/.test(x.episodeUrl || ''));
        if (!list.length) throw new Error('empty');
        return list;
      })
      .finally(() => timer && clearTimeout(timer));
    p.catch(() => cache.delete(show.id)); // a failed show gets asked again next time
    cache.set(show.id, p);
    return p;
  };

  const light = i => tiles.forEach((t, k) => t.classList.toggle('on', k === i));
  const setState = s => { root.dataset.state = s; };
  let pos = 0, spinning = false, lastEpisode = '', level = () => {};

  function spin() {
    if (spinning) return;
    spinning = true;
    spinBtn.disabled = true; again.disabled = true;
    audio.pause();
    card.hidden = true; card.classList.remove('in');
    hubCover.hidden = true;
    setState('spinning');

    const target = rand(N), show = shows[target];
    const list = episodes(show); // starts loading now, while the wheel turns
    const start = pos, base = start - (start % N);
    let end = base + (reduce ? 0 : 3 * N) + target;
    if (end <= start) end += N;

    if (reduce) { // no sweep: light the show and go straight to the episode
      comet.style.transform = `rotate(${end * STEP}deg)`;
      light(target); pos = end; land(show, list);
      return;
    }
    const D = 4200 + rand(700), t0 = performance.now();
    const ease = t => 1 - Math.pow(1 - t, 4); // fast off the mark, long slow finish
    let shown = -1;
    const frame = now => {
      const t = Math.min(1, (now - t0) / D), p = start + (end - start) * ease(t);
      comet.style.transform = `rotate(${p * STEP}deg)`;
      const i = ((Math.round(p) % N) + N) % N;
      if (i !== shown) { shown = i; light(i); ticker.textContent = shows[i].name; }
      if (t < 1) requestAnimationFrame(frame);
      else { pos = end; land(show, list); }
    };
    requestAnimationFrame(frame);
  }

  const replay = (el, cls) => { el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls); };
  function land(show, list) {
    const i = shows.indexOf(show);
    light(i);
    if (!reduce) { replay(tiles[i], 'burst'); replay(shock, 'go'); }
    ticker.textContent = 'Tuning in…';
    setState('loading');
    list.then(eps => {
      let ep = eps[rand(eps.length)];
      if (eps.length > 1) while (ep.episodeUrl === lastEpisode) ep = eps[rand(eps.length)];
      lastEpisode = ep.episodeUrl;
      fill(show, ep);
    }, () => fill(show, null));
  }

  function fill(show, ep) {
    cover.src = art(show, 200); cover.alt = '';
    hubCover.src = art(show, 400); hubCover.alt = show.name; hubCover.hidden = false;
    showName.textContent = show.name;
    if (ep) {
      meta.textContent = `${minutes(ep.trackTimeMillis || 0)}, ${day(ep.releaseDate)}`;
      title.textContent = ep.trackName;
      audio.src = ep.episodeUrl; audio.hidden = false;
      apple.href = (ep.trackViewUrl || show.apple).split('?')[0];
      live.textContent = `${show.name}: ${ep.trackName}, ${minutes(ep.trackTimeMillis || 0)}.`;
    } else {
      meta.textContent = show.host;
      title.textContent = 'This show isn’t answering right now. Spin again, or open it in Apple Podcasts.';
      audio.removeAttribute('src'); audio.hidden = true;
      apple.href = show.apple;
      live.textContent = `${show.name}. The episode list didn’t load.`;
    }
    setState('landed');
    level();
    card.hidden = false;
    void card.offsetWidth; card.classList.add('in');
    spinning = false; spinBtn.disabled = false; again.disabled = false;
    // Keyboard and screen-reader users land on the episode; on phones, bring the card into view.
    title.focus({preventScroll: true});
    if (getComputedStyle(card).position !== 'absolute') {
      const r = card.getBoundingClientRect();
      if (r.bottom > innerHeight || r.top < 0) card.scrollIntoView({behavior: reduce ? 'auto' : 'smooth', block: 'center'});
    }
  }

  // The wheel leans a few degrees toward the pointer, eased so it drifts rather than snaps.
  if (!reduce && window.matchMedia && matchMedia('(hover: hover) and (pointer: fine)').matches) {
    let tx = 0, ty = 0, x = 0, y = 0, raf = 0;
    const step = () => {
      x += (tx - x) * 0.08; y += (ty - y) * 0.08;
      tilt.style.transform = `rotateX(${(-y * 7).toFixed(2)}deg) rotateY(${(x * 7).toFixed(2)}deg)`;
      raf = Math.abs(tx - x) + Math.abs(ty - y) > 0.001 ? requestAnimationFrame(step) : 0;
    };
    const go = () => { if (!raf) raf = requestAnimationFrame(step); };
    root.addEventListener('pointermove', e => {
      if (e.pointerType !== 'mouse' || root.dataset.state === 'landed') return; // level while you read
      const r = stage.getBoundingClientRect();
      tx = Math.max(-1, Math.min(1, (e.clientX - r.left) / r.width * 2 - 1));
      ty = Math.max(-1, Math.min(1, (e.clientY - r.top) / r.height * 2 - 1));
      go();
    });
    root.addEventListener('pointerleave', () => { tx = 0; ty = 0; go(); });
    level = () => { tx = 0; ty = 0; go(); };
  }

  spinBtn.addEventListener('click', spin);
  again.addEventListener('click', spin);
  // Warm the covers so the first sweep doesn't wait on images.
  for (const s of shows) { const im = new Image(); im.src = art(s, 200); }
})();
