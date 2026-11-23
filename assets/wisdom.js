// Daily Dose of Wisdom: a light runs round seven podcasts, slows down, and stops on one.
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
  const card = $('.wz-card'), cover = $('.wz-cover'), showName = $('.wz-show-name'), meta = $('.wz-meta');
  const title = $('.wz-ep'), audio = $('.wz-audio'), again = $('.wz-again'), apple = $('.wz-apple'), live = $('.wz-live');

  // The entrance is pure CSS; take the overlay away once it has played so it never sits over the page.
  const portal = document.querySelector('.wz-portal');
  if (portal) setTimeout(() => portal.remove(), reduce ? 0 : 1600);

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
  let pos = 0, spinning = false, lastEpisode = '';

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

  function land(show, list) {
    light(shows.indexOf(show));
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

  spinBtn.addEventListener('click', spin);
  again.addEventListener('click', spin);
  // Warm the covers so the first sweep doesn't wait on images.
  for (const s of shows) { const im = new Image(); im.src = art(s, 200); }
})();
