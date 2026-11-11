/* "More Stories" at the end of an article: 3 random other articles from the whole collection.
   Reads the Jekyll-generated /articles.json. The server-rendered cards stay if this fails. */
(function () {
  var grid = document.getElementById('more-stories');
  if (!grid) return;
  var feed = grid.getAttribute('data-feed') || '/articles.json';
  var current = grid.getAttribute('data-current');

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function card(a) {
    var art = el('article', 'related-card');
    var h3 = el('h3');
    var link = el('a', '', a.headline);
    link.href = a.url;
    h3.appendChild(link);
    art.appendChild(el('span', 'category', a.section));
    art.appendChild(h3);
    art.appendChild(el('p', '', a.summary));
    return art;
  }
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }

  fetch(feed, { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var pool = (data.articles || []).filter(function (a) { return a.url !== current; });
      if (!pool.length) return;
      grid.replaceChildren.apply(grid, shuffle(pool).slice(0, 3).map(card));
    })
    .catch(function () { /* keep the server-rendered cards */ });
})();
