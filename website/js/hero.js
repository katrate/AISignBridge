/* ============================================================
   AI Sign Bridge — Cinematic Frame (Remake v2)
   Top nav = pages · bottom switcher = sections (no scroll)
   Background videos auto-cycle behind the frame.
   ============================================================ */

(function () {
  'use strict';

  var hero = document.getElementById('hmHero');
  if (!hero) return;

  // ====== PAGES & SECTIONS ======
  var PAGES = {
    // The Download section stays in the home page (reachable via the
    // navbar's "Download App" button, data-go="home:1") but has no
    // tab in the bottom switcher — the switcher shows only Overview.
    home:     { label: 'Home',         sections: ['Overview'] },
    features: { label: 'Features',     sections: ['Highlights', 'In Depth'] },
    how:      { label: 'How It Works', sections: ['Pipeline', 'Bidirectional', 'Training'] },
    learn:    { label: 'Learn ASL',    sections: ['Fingerspell', 'Tips'] },
    about:    { label: 'About',        sections: ['Mission', 'Values', 'Roadmap'] }
  };

  var currentPage = 'home';
  var currentSection = 0;

  var stage = document.getElementById('hmStage');
  var switcher = document.getElementById('hmSwitcher');
  var pages = {};
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('.hm-nav-link'));
  var menuLinks = Array.prototype.slice.call(document.querySelectorAll('.hm-menu-link'));

  // Gather page elements
  Object.keys(PAGES).forEach(function (name) {
    pages[name] = stage.querySelector('.hm-page[data-page="' + name + '"]');
  });

  function goToPage(name, section) {
    if (!PAGES[name]) return;

    // Same page: jump straight to the requested section
    // (re-clicking a nav link resets the page to its first section)
    if (name === currentPage) {
      if (section == null) goToSection(0);
      else goToSection(section);
      return;
    }

    currentPage = name;
    currentSection = section != null ? section : 0;

    Object.keys(pages).forEach(function (p) {
      pages[p].classList.toggle('active', p === name);
    });

    // Activate the target section
    var secs = pages[name].querySelectorAll('.hm-section');
    secs.forEach(function (s, i) {
      s.classList.toggle('active', i === currentSection);
    });

    // Nav + menu active states
    navLinks.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-page') === name); });
    menuLinks.forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-page') === name); });

    // Gently focus the fingerspell input when opening Learn on desktop
    if (name === 'learn' && window.matchMedia('(min-width: 768px)').matches) {
      var ti = document.getElementById('textInput');
      if (ti) window.setTimeout(function () { ti.focus(); }, 520);
    }

    renderSwitcher();
  }

  function goToSection(i) {
    var secs = pages[currentPage].querySelectorAll('.hm-section');
    if (i < 0 || i >= secs.length || i === currentSection) return;
    currentSection = i;
    secs.forEach(function (s, idx) {
      s.classList.toggle('active', idx === i);
    });
    renderSwitcher();
  }

  // ====== SECTION SWITCHER (rebuilt per page) ======
  function renderSwitcher() {
    if (!switcher) return;
    switcher.innerHTML = '';
    PAGES[currentPage].sections.forEach(function (name, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.role = 'tab';
      b.className = 'hm-switch-btn' + (i === currentSection ? ' active' : '');
      b.setAttribute('aria-selected', i === currentSection ? 'true' : 'false');
      b.textContent = name;
      b.addEventListener('click', function () { goToSection(i); });
      switcher.appendChild(b);
    });
  }

  // ====== NAVIGATION WIRING ======
  // Nav pill, logo, ghost CTA + mobile menu buttons switch pages.
  // Scoped to buttons only — the .hm-page section divs also carry data-page.
  var pageButtons = Array.prototype.slice.call(document.querySelectorAll('button[data-page]'));
  pageButtons.forEach(function (b) {
    b.addEventListener('click', function () {
      goToPage(b.getAttribute('data-page'));
      closeMenu();
    });
  });

  // "data-go" buttons jump to a page + section, e.g. data-go="home:1"
  document.querySelectorAll('[data-go]').forEach(function (b) {
    b.addEventListener('click', function () {
      var parts = b.getAttribute('data-go').split(':');
      var sec = parts[1] != null ? parseInt(parts[1], 10) : 0;
      if (isNaN(sec)) sec = 0;
      goToPage(parts[0], sec);
      closeMenu();
    });
  });

  // ====== BACKGROUND VIDEOS: AUTO-CYCLE ======
  var videos = Array.prototype.slice.call(hero.querySelectorAll('.hm-video'));
  var videoIdx = 0;
  var videoTimer = null;

  function cycleVideo() {
    if (videos.length < 2) return;
    videoIdx = (videoIdx + 1) % videos.length;
    videos.forEach(function (v, i) {
      v.classList.toggle('active', i === videoIdx);
    });
  }

  if (videos.length > 1) {
    videoTimer = window.setInterval(cycleVideo, 20000);
    // Reduce background video motion when the page is hidden
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        window.clearInterval(videoTimer);
        videoTimer = null;
      } else if (!videoTimer) {
        videoTimer = window.setInterval(cycleVideo, 20000);
      }
    });
  }

  // ====== LEARN — FINGERSPELLING TOOL ======
  function initFingerspell() {
    var input = document.getElementById('textInput');
    if (!input) return;
    var strip = document.getElementById('signStrip');
    var empty = document.getElementById('signEmpty');
    var clearBtn = document.getElementById('clearBtn');
    var charCount = document.getElementById('charCount');

    function isSupported(c) {
      var up = c.toUpperCase();
      return (up >= 'A' && up <= 'Z') || (up >= '0' && up <= '9');
    }

    function build(text) {
      var chars = [];
      for (var i = 0; i < text.length; i++) {
        var c = text[i];
        if (c === ' ' || isSupported(c)) chars.push(c.toUpperCase());
      }
      if (charCount) charCount.textContent = text.length;

      if (chars.length === 0) {
        strip.style.display = 'none';
        empty.style.display = 'block';
        return;
      }
      empty.style.display = 'none';
      strip.style.display = 'flex';
      strip.innerHTML = '';

      chars.forEach(function (c, idx) {
        var tile = document.createElement('div');
        tile.className = 'hm-sign-tile hm-glass';
        tile.style.animationDelay = (idx * 0.04) + 's';

        if (c === ' ') {
          tile.innerHTML = '<div class="hm-tile-space">⸻</div>';
        } else {
          var img = document.createElement('img');
          img.src = 'signs/' + c + '.jpg';
          img.alt = 'ASL sign for ' + c;
          img.loading = 'lazy';
          img.onerror = function () {
            this.outerHTML = '<div class="hm-tile-space">🖐️</div>';
          };
          tile.appendChild(img);
          var label = document.createElement('div');
          label.className = 'hm-tile-label';
          label.textContent = c;
          tile.appendChild(label);
        }
        strip.appendChild(tile);
      });
    }

    input.addEventListener('input', function () { build(this.value); });
    clearBtn.addEventListener('click', function () {
      input.value = '';
      input.focus();
      build('');
    });
    document.querySelectorAll('.hm-chip').forEach(function (chip) {
      chip.addEventListener('click', function () {
        input.value = chip.getAttribute('data-text');
        build(input.value);
        input.focus();
      });
    });
    build('');
  }

  // ====== MOBILE MENU ======
  var menuBtn = document.getElementById('hmMenuBtn');
  var menu = document.getElementById('hmMenu');

  function closeMenu() {
    if (!menu || !menuBtn) return;
    menu.classList.remove('open');
    menuBtn.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
    menu.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  if (menuBtn && menu) {
    menuBtn.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      menuBtn.classList.toggle('open', open);
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      menu.setAttribute('aria-hidden', open ? 'false' : 'true');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeMenu();
    });
  }

  // ====== THEME TOGGLE MIRROR (desktop + mobile) ======
  var themePrimary = document.getElementById('themeToggle');
  var themeMirrors = Array.prototype.slice.call(document.querySelectorAll('[data-theme-toggle-mirror]'));
  if (themePrimary && themeMirrors.length) {
    themeMirrors.forEach(function (m) {
      m.addEventListener('click', function () { themePrimary.click(); });
      m.textContent = themePrimary.textContent;
    });
    var syncIcons = function () {
      themeMirrors.forEach(function (m) { m.textContent = themePrimary.textContent; });
    };
    var observer = new MutationObserver(syncIcons);
    observer.observe(themePrimary, { childList: true, characterData: true, subtree: true });
    syncIcons();
  }

  // ====== INIT ======
  initFingerspell();
  renderSwitcher();

  // ── Deep-link: open the page named in ?page=xxx (used by redirect pages) ──
  (function () {
    var param = new URLSearchParams(window.location.search).get('page');
    if (param && param !== 'home') {
      // Small delay so the DOM is fully painted before switching
      window.setTimeout(function () { goToPage(param); }, 80);
    }
  })();
})();
