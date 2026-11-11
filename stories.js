/* Shared by index.html (random stories) and archive.html (full archive).
   Reads articles.json. Articles with "featured": true live on the front page
   and are excluded from both the archive and the random picks. */
(function () {
  var clean = function (p) { return String(p || '').replace(/^\//, ''); };

  function fmt(iso) {
    var d = new Date(String(iso) + 'T00:00:00Z');
    if (isNaN(d)) return '';
    return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;   // textContent, never innerHTML: CMS content stays inert
    return n;
  }

  function card(a) {
    var art = el('article', 'article-card');

    var imgWrap = el('div', 'story-image');
    var img = el('img', a.fit_image ? 'fit-image' : '');
    img.src = clean(a.image);
    img.alt = a.image_alt || '';
    img.loading = 'lazy';
    imgWrap.appendChild(img);

    var body = el('div', 'story-content');
    var h3 = el('h3');
    var link = el('a', 'headline-link', a.headline);
    link.href = clean(a.url);
    h3.appendChild(link);
    body.appendChild(el('span', 'category', a.category));
    body.appendChild(h3);
    body.appendChild(el('p', '', a.summary));
    body.appendChild(el('span', 'byline', 'By ' + a.author + ' · ' + fmt(a.date)));

    art.appendChild(imgWrap);
    art.appendChild(body);
    return art;
  }

  function shuffle(arr) {                      // Fisher-Yates
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  var random = document.getElementById('random-stories');
  var archive = document.getElementById('archive-grid');
  if (!random && !archive) return;

  fetch('articles.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var pool = (data.articles || []).filter(function (a) { return !a.featured; });

      if (random && pool.length) {
        var picks = shuffle(pool.slice()).slice(0, 3).map(card);
        random.replaceChildren.apply(random, picks);
      }

      if (archive) {
        pool.sort(function (a, b) { return String(b.date).localeCompare(String(a.date)); });
        if (!pool.length) {
          archive.replaceChildren(el('p', 'archive-note', 'Nothing in the archive yet.'));
        } else {
          archive.replaceChildren.apply(archive, pool.map(card));
        }
      }
    })
    .catch(function () {
      // index.html keeps its static fallback cards; the archive shows a message
      if (archive) archive.replaceChildren(el('p', 'archive-note', 'Couldn\u2019t load the archive. Try refreshing.'));
    });
})();
