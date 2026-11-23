// daily dose of wisdom: a light runs round seven podcasts, slows down, and stops on one.
// While it turns, the page asks Apple Podcasts for that show's recent episodes and picks one at random.
(() => {
  const root = document.querySelector('.wz');
  const data = document.getElementById('wz-data');
  if (!root || !data) return;

  const shows = JSON.parse(data.textContent);
  const N = shows.length, STEP = 360 / N;
  const reduce = false; // the page's motion plays for everyone, whatever the device's reduce-motion setting
  const $ = s => root.querySelector(s);
  const tiles = [...root.querySelectorAll('.wz-show')];
  const comet = $('.wz-comet'), spinBtn = $('.wz-spin'), ticker = $('.wz-ticker'), hubCover = $('.wz-hub-cover');
  const shock = $('.wz-shock'), stage = $('.wz-stage'), tilt = $('.wz-tilt');
  const card = $('.wz-card'), cover = $('.wz-cover'), showName = $('.wz-show-name'), meta = $('.wz-meta');
  const title = $('.wz-ep'), audio = $('.wz-audio'), again = $('.wz-again'), apple = $('.wz-apple'), live = $('.wz-live');

  const html = document.documentElement;
  const rnd = (a, b) => a + Math.random() * (b - a);

  // ---------- The way in: a jump to hyperspace, timed off the CSS fade of the overlay ----------
  // Stars live in 3D in front of you and fly toward the screen. Seen in perspective they rush outward from the
  // centre; each is drawn as a line from where it is now back to where it was a moment ago, so the faster you go,
  // the longer the streaks. The centre stays dark because the far stars there are faint and barely move.
  const portal = document.querySelector('.wz-portal');
  if (portal) {
    const done = () => { if (portal.isConnected) portal.remove(); };
    if (reduce || !html.classList.contains('portal')) done();
    else {
      const cv = portal.querySelector('.wz-jump'), c = cv.getContext && cv.getContext('2d');
      const fade = portal.getAnimations ? portal.getAnimations()[0] : null;
      const t0 = performance.now();
      const clock = () => (fade && fade.currentTime != null ? fade.currentTime : performance.now() - t0) / 1000;
      let running = !!c;
      if (c) {
        const D = Math.min(1.5, devicePixelRatio || 1), W = innerWidth, H = innerHeight, cx = W / 2, cy = H / 2;
        cv.width = W * D; cv.height = H * D; c.setTransform(D, 0, 0, D, 0, 0);
        const F = Math.max(W, H) * 0.55, NEAR = 0.03, END = 2.65;
        // Speed through the field (depth units per second): a slow drift, then a long build to full speed.
        const speed = t => {
          if (t < 0.3) return 0.06;
          const k = Math.min(1, (t - 0.3) / 1.55);
          return 0.06 + 3.6 * k * k * k;
        };
        const n = Math.max(300, Math.min(1100, Math.round(W * H / 1200)));
        const spawn = (s, deep) => {
          s.x = rnd(-1, 1); s.y = rnd(-1, 1); s.z = deep ? rnd(0.05, 1) : rnd(0.75, 1);
          s.tone = Math.random() < 0.8 ? 0 : 1;
          return s;
        };
        const stars = Array.from({length: n}, () => spawn({}, true));
        const BINS = 8, tones = ['233,228,218', '255,250,242'];
        const paths = Array.from({length: BINS * 2}, () => []);
        let last = clock();
        const frame = () => {
          if (!running) return;
          const t = clock(), dt = Math.min(0.05, Math.max(0, t - last)); last = t;
          const v = speed(t), trail = Math.max(0.004, v * 0.07);
          const lift = Math.min(1, t / 0.25); // stars fade in over the first beat
          const calm = 1 - Math.min(1, Math.max(0, t - 0.3) / 1.2); // far stars are easy to see at rest, faint at speed
          for (const p of paths) p.length = 0;
          for (const s of stars) {
            s.z -= v * dt;
            const x1 = cx + s.x / s.z * F, y1 = cy + s.y / s.z * F;
            if (s.z < NEAR || x1 < -40 || x1 > W + 40 || y1 < -40 || y1 > H + 40) { spawn(s, false); continue; }
            const zt = Math.min(1.05, s.z + trail);
            const x0 = cx + s.x / zt * F, y0 = cy + s.y / zt * F;
            const near = 1 - s.z; // 0 far .. 1 close
            const bin = Math.min(BINS - 1, Math.floor(near * BINS));
            paths[bin * 2 + s.tone].push(x0, y0, x1, y1);
          }
          c.clearRect(0, 0, W, H);
          c.lineCap = 'round';
          for (let b = 0; b < BINS; b++) {
            const near = (b + 0.5) / BINS;
            const alpha = lift * Math.min(1, 0.08 + 0.42 * calm + near * near * 1.25);
            c.lineWidth = 0.5 + near * near * 2.2;
            for (let k = 0; k < 2; k++) {
              const seg = paths[b * 2 + k];
              if (!seg.length) continue;
              c.strokeStyle = `rgba(${tones[k]},${alpha.toFixed(3)})`;
              c.beginPath();
              for (let i = 0; i < seg.length; i += 4) { c.moveTo(seg[i], seg[i + 1]); c.lineTo(seg[i + 2], seg[i + 3]); }
              c.stroke();
            }
          }
          if (t < END) requestAnimationFrame(frame); else running = false;
        };
        requestAnimationFrame(frame);
      }
      const skip = () => { running = false; html.classList.add('portal-skip'); done(); };
      portal.addEventListener('pointerdown', skip, {once: true});
      addEventListener('keydown', function k(e) { if (!portal.isConnected) return removeEventListener('keydown', k); if (!e.metaKey && !e.ctrlKey && !e.altKey) skip(); });
      // Take the overlay away when its fade ends; if the browser can't say, or the fade is cancelled, after a few seconds anyway.
      const finish = () => { running = false; done(); };
      if (fade && fade.finished) fade.finished.then(finish, finish);
      setTimeout(finish, fade && fade.finished ? 6000 : 3000);
    }
  }

  // ---------- The sky: drifting slowly, as if floating through space ----------
  // Every star has a depth: near ones drift a little faster than far ones, so the field has parallax.
  // They breathe a little, one brightens now and then, and once in a while one falls.
  // Kept quiet on purpose: enough to show the sky is alive, never enough to pull the eye off the wheel.
  const sky = document.querySelector('.wz-sky');
  const ctx = sky && sky.getContext && sky.getContext('2d');
  if (ctx) {
    const tones = ['255,250,240', '255,238,212', '233,228,218', '255,214,160'];
    let W = 0, H = 0, stars = [], meteors = [], nextMeteor = performance.now() + rnd(5000, 9000), lastDraw = 0, lastT = 0;
    const DRIFT = 8, DX = -0.94, DY = -0.34; // px per second for the nearest stars, heading up and to the left
    const build = () => {
      const D = Math.min(1.5, devicePixelRatio || 1);
      W = innerWidth; H = innerHeight; sky.width = W * D; sky.height = H * D; ctx.setTransform(D, 0, 0, D, 0, 0);
      stars = Array.from({length: Math.min(260, Math.round(W * H / 6500))}, () => {
        const z = Math.pow(Math.random(), 1.6) * 0.85 + 0.15; // most stars are far away
        return {x: Math.random() * W, y: Math.random() * H, z,
          r: z > 0.8 && Math.random() < 0.5 ? rnd(1.05, 1.7) : rnd(0.35, 0.95) * (0.7 + 0.4 * z),
          a: rnd(0.12, 0.55) * (0.65 + 0.35 * z), s: rnd(0.15, 0.55), p: rnd(0, 6.283), c: tones[Math.floor(Math.random() * tones.length)], f: 0, fd: 0};
      });
    };
    const draw = now => {
      const dt = lastT ? Math.min(0.1, (now - lastT) / 1000) : 0; lastT = now;
      ctx.clearRect(0, 0, W, H);
      for (const s of stars) {
        if (dt) { // drift, and come back in on the far side
          s.x += DX * DRIFT * s.z * dt; s.y += DY * DRIFT * s.z * dt;
          if (s.x < -4) s.x += W + 8; else if (s.x > W + 4) s.x -= W + 8;
          if (s.y < -4) s.y += H + 8; else if (s.y > H + 4) s.y -= H + 8;
        }
        let k = 0;
        if (!s.f && Math.random() < 0.00003) { s.f = now; s.fd = rnd(1400, 2400); } // about one star every few seconds brightens
        if (s.f) { const q = (now - s.f) / s.fd; if (q >= 1) s.f = 0; else k = Math.sin(Math.PI * q); }
        const tw = s.a * (0.85 + 0.15 * Math.sin(now / 1000 * s.s + s.p));
        const al = Math.min(1, tw + k * 0.45), r = s.r * (1 + k * 0.35);
        ctx.fillStyle = `rgba(${s.c},${al.toFixed(3)})`;
        ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, 6.283); ctx.fill();
      }
      if (now > nextMeteor) { // a shooting star, from the top half, slanting down either way
        const dir = Math.random() < 0.5 ? -1 : 1, ang = rnd(0.32, 0.62), sp = rnd(800, 1300);
        meteors.push({x: rnd(W * 0.15, W * 0.85), y: rnd(-20, H * 0.35), vx: Math.cos(ang) * sp * dir, vy: Math.sin(ang) * sp, len: rnd(140, 280), t0: now, life: rnd(700, 1100)});
        nextMeteor = now + rnd(12000, 22000);
      }
      meteors = meteors.filter(m => now - m.t0 < m.life);
      for (const m of meteors) {
        const e = (now - m.t0) / 1000, q = (now - m.t0) / m.life, al = 0.7 * Math.sin(Math.PI * q);
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
        // Full rate while a star is falling, half rate otherwise (the drift is slow enough for that),
        // and a quarter rate while the wheel spins so the spin gets nearly every frame.
        const busy = root.dataset.state === 'spinning';
        if (busy) nextMeteor = Math.max(nextMeteor, now + 1500);
        if (meteors.length || now - lastDraw > (busy ? 64 : 32)) { draw(now); lastDraw = now; }
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
  if (!reduce) { // only mouse movement drives it (checked per event), so touch screens never tilt
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
