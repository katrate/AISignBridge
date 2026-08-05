

(function () {
  'use strict';

  
  
  
  function initThreeScene() {
    if (typeof THREE === 'undefined') return;
    const canvas = document.getElementById('three-canvas');
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x06060e, 0);
    const darkClear = new THREE.Color(0x06060e);
    const lightClear = new THREE.Color('#f5f0e8');
    const clearColor = new THREE.Color();
    let themeFactor = 1.0;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 0, 18);
    camera.lookAt(0, 0, 0);

    const clock = new THREE.Clock();

    
    const palette = {
      deepNavy:  new THREE.Color('#06060e'),
      accentIris: new THREE.Color('#6366f1'),
      accentCoral: new THREE.Color('#f43f5e'),
      accentGold: new THREE.Color('#f59e0b'),
      deepIndigo: new THREE.Color('#4338ca'),
      warmCream: new THREE.Color('#ece8f0'),
      deepPurple: new THREE.Color('#3730a3'),
    };

    
    
    const ribbons = [];
    const ribbonCount = 6;

    function createRibbon(color, baseX, baseY, baseZ, scaleFactor) {
      const segments = 40;
      const points = [];
      for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const x = baseX + Math.sin(t * Math.PI * 4) * 2 * scaleFactor;
        const y = baseY + Math.cos(t * Math.PI * 3) * 1.5 * scaleFactor;
        const z = baseZ + Math.sin(t * Math.PI * 2) * 1.5 * scaleFactor;
        points.push(new THREE.Vector3(x, y, z));
      }

      const curve = new THREE.CatmullRomCurve3(points);
      const curvePoints = curve.getPoints(60);

      
      const geometry = new THREE.BufferGeometry();
      const posArray = new Float32Array(curvePoints.length * 3);
      curvePoints.forEach(function(p, i) {
        posArray[i * 3] = p.x;
        posArray[i * 3 + 1] = p.y;
        posArray[i * 3 + 2] = p.z;
      });
      geometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

      const ribbonBaseOpacity = 0.08 + Math.random() * 0.07;
      const material = new THREE.LineBasicMaterial({
        color: color,
        transparent: true,
        opacity: ribbonBaseOpacity,
      });

      const line = new THREE.Line(geometry, material);
      line.userData = {
        basePoints: points,
        speed: 0.1 + Math.random() * 0.15,
        phase: Math.random() * Math.PI * 2,
        amp: 0.3 + Math.random() * 0.5,
        color: color,
        baseX: baseX,
        baseY: baseY,
        baseZ: baseZ,
        scaleFactor: scaleFactor,
        isMain: true,
        baseOpacity: ribbonBaseOpacity,
      };
      scene.add(line);
      ribbons.push(line);

      
      const pos2 = new Float32Array(posArray);
      
      for (let i = 0; i < curvePoints.length; i++) {
        pos2[i * 3] += 0.3;
        pos2[i * 3 + 1] -= 0.3;
      }
      const geo2 = new THREE.BufferGeometry();
      geo2.setAttribute('position', new THREE.BufferAttribute(pos2, 3));
      const mat2 = new THREE.LineBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.03,
      });
      const line2 = new THREE.Line(geo2, mat2);
      
      line2.userData = { isDepth: true, baseOpacity: 0.03 };
      scene.add(line2);
      ribbons.push(line2);

      return { line, line2 };
    }

    
    const ribbonConfigs = [
      { color: palette.accentIris,  x: -3, y: 1,  z: -3, scale: 1.0 },
      { color: palette.accentCoral, x: 3,  y: -1, z: -4, scale: 0.9 },
      { color: palette.accentGold,  x: -2, y: -2, z: -5, scale: 0.8 },
      { color: palette.deepIndigo,  x: 4,  y: 2,  z: -6, scale: 1.1 },
      { color: palette.deepPurple,  x: -4, y: 3,  z: -7, scale: 0.7 },
      { color: palette.accentCoral, x: 0,  y: -3, z: -8, scale: 1.0 },
    ];

    ribbonConfigs.forEach(function(cfg) {
      createRibbon(cfg.color, cfg.x, cfg.y, cfg.z, cfg.scale);
    });

    
    
    const orbs = [];
    const orbCount = 8;

    for (let i = 0; i < orbCount; i++) {
      const radius = 0.15 + Math.random() * 0.4;
      const geo = new THREE.SphereGeometry(radius, 16, 16);
      const mat = new THREE.MeshBasicMaterial({
        color: [palette.accentIris, palette.accentCoral, palette.accentGold, palette.deepIndigo][Math.floor(Math.random() * 4)],
        transparent: true,
        opacity: 0.08 + Math.random() * 0.08,
      });
      const mesh = new THREE.Mesh(geo, mat);

      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const dist = 3 + Math.random() * 6;

      mesh.position.set(
        dist * Math.sin(phi) * Math.cos(theta),
        dist * Math.cos(phi),
        dist * Math.sin(phi) * Math.sin(theta) - 2
      );

      mesh.userData = {
        baseX: mesh.position.x,
        baseY: mesh.position.y,
        baseZ: mesh.position.z,
        speed: 0.1 + Math.random() * 0.2,
        phase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.5 + Math.random() * 0.5,
        pulsePhase: Math.random() * Math.PI * 2,
        baseOpacity: mat.opacity,
        floatAmp: 0.2 + Math.random() * 0.4,
      };

      scene.add(mesh);
      orbs.push(mesh);
    }

    
    
    const dustCount = 400;
    const dustGeo = new THREE.BufferGeometry();
    const dustPos = new Float32Array(dustCount * 3);
    const dustSizes = new Float32Array(dustCount);

    for (let i = 0; i < dustCount; i++) {
      dustPos[i * 3] = (Math.random() - 0.5) * 30;
      dustPos[i * 3 + 1] = (Math.random() - 0.5) * 20;
      dustPos[i * 3 + 2] = (Math.random() - 0.5) * 20 - 5;
      dustSizes[i] = 0.02 + Math.random() * 0.04;
    }

    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    dustGeo.setAttribute('size', new THREE.BufferAttribute(dustSizes, 1));

    const dustMat = new THREE.PointsMaterial({
      color: 0xece8f0,
      size: 0.035,
      transparent: true,
      opacity: 0.15,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });
    const dust = new THREE.Points(dustGeo, dustMat);
    scene.add(dust);

    
    
    const washMat = new THREE.MeshBasicMaterial({
      color: 0x6366f1,
      transparent: true,
      opacity: 0.02,
      side: THREE.DoubleSide,
    });
    const washGeo = new THREE.PlaneGeometry(18, 12);
    const wash = new THREE.Mesh(washGeo, washMat);
    wash.position.set(0, 0, -8);
    scene.add(wash);

    const wash2Mat = new THREE.MeshBasicMaterial({
      color: 0xf59e0b,
      transparent: true,
      opacity: 0.015,
      side: THREE.DoubleSide,
    });
    const wash2 = new THREE.Mesh(washGeo.clone(), wash2Mat);
    wash2.position.set(1, -1, -9);
    wash2.rotation.z = 0.3;
    scene.add(wash2);

    
    let mouseX = 0, mouseY = 0;
    let smoothX = 0, smoothY = 0;

    document.addEventListener('mousemove', function (e) {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    
    function animate() {
      requestAnimationFrame(animate);
      const t = clock.getElapsedTime();

      
      const isLight = document.documentElement.getAttribute('data-theme') === 'light';
      const targetFactor = isLight ? 0.4 : 1.0;
      themeFactor += (targetFactor - themeFactor) * 0.03;

      
      clearColor.copy(darkClear).lerp(lightClear, 1 - themeFactor);
      renderer.setClearColor(clearColor, 0);

      
      smoothX += (mouseX - smoothX) * 0.02;
      smoothY += (mouseY - smoothY) * 0.02;

      
      camera.position.x = smoothX * 0.5;
      camera.position.y = smoothY * 0.3;
      camera.lookAt(0, 0, 0);

      
      ribbons.forEach(function(rib) {
        const ud = rib.userData;
        if (!ud || !ud.basePoints || ud.isDepth) return;

        
        var newPts = [];
        ud.basePoints.forEach(function(p, i) {
          var tt = i / 40;
          var wave = Math.sin(t * ud.speed + tt * Math.PI * 2 + ud.phase) * ud.amp;
          var wave2 = Math.cos(t * ud.speed * 0.7 + tt * Math.PI * 3 + ud.phase) * ud.amp * 0.5;
          newPts.push(new THREE.Vector3(
            p.x + wave * 0.5 + smoothX * 0.2,
            p.y + wave2 * 0.5 + smoothY * 0.15,
            p.z + Math.sin(t * ud.speed * 0.5 + tt * Math.PI + ud.phase) * 0.3
          ));
        });

        
        var newCurve = new THREE.CatmullRomCurve3(newPts);
        var smoothPts = newCurve.getPoints(60);

        
        var pos = rib.geometry.attributes.position.array;
        smoothPts.forEach(function(pt, i) {
          pos[i * 3] = pt.x;
          pos[i * 3 + 1] = pt.y;
          pos[i * 3 + 2] = pt.z;
        });
        rib.geometry.attributes.position.needsUpdate = true;
      });

      
      ribbons.forEach(function(rib) {
        if (rib.userData && rib.userData.baseOpacity != null) {
          rib.material.opacity = rib.userData.baseOpacity * themeFactor;
        }
      });

      
      orbs.forEach(function(orb) {
        const ud = orb.userData;
        orb.position.x = ud.baseX + Math.sin(t * ud.speed + ud.phase) * ud.floatAmp;
        orb.position.y = ud.baseY + Math.cos(t * ud.speed * 0.8 + ud.phase) * ud.floatAmp * 0.7;
        orb.position.z = ud.baseZ + Math.sin(t * ud.speed * 0.6 + ud.phase + 1) * ud.floatAmp * 0.5;
        const pulse = 0.5 + 0.5 * Math.sin(t * ud.pulseSpeed + ud.pulsePhase);
        orb.material.opacity = ud.baseOpacity * (0.6 + 0.4 * pulse) * themeFactor;
        const s = 0.8 + 0.2 * pulse;
        orb.scale.set(s, s, s);
      });

      
      dust.rotation.y += 0.0002;
      dust.rotation.x += 0.0001;
      dustMat.opacity = 0.15 * themeFactor;

      
      wash.position.x = Math.sin(t * 0.05) * 0.3;
      wash.position.y = Math.cos(t * 0.04) * 0.3;
      wash.material.opacity = (0.015 + 0.01 * Math.sin(t * 0.1)) * themeFactor;
      wash2.position.x = Math.sin(t * 0.04 + 1) * 0.3;
      wash2.position.y = Math.cos(t * 0.05 + 1) * 0.3;
      wash2.material.opacity = 0.015 * themeFactor;

      renderer.render(scene, camera);
    }

    animate();

    
    window.addEventListener('resize', function () {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  
  function initScrollProgress() {
    var bar = document.getElementById('scroll-progress');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'scroll-progress';
      document.body.prepend(bar);
    }

    window.addEventListener('scroll', function () {
      var scrollTop = window.scrollY;
      var docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      var progress = (scrollTop / docHeight) * 100;
      bar.style.width = progress + '%';
    });
  }

  
  function initScrollReveal() {
    var revealSelectors = '.reveal, .reveal-left, .reveal-right, .reveal-scale';
    var reveals = document.querySelectorAll(revealSelectors);
    if (reveals.length === 0) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    reveals.forEach(function (el) {
      observer.observe(el);
    });
  }

  
  function initNavbar() {
    var navbar = document.getElementById('navbar');
    if (!navbar) return;

    window.addEventListener('scroll', function () {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  
  function initMobileMenu() {
    var btn = document.getElementById('mobileMenuBtn');
    var links = document.getElementById('navLinks');
    if (!btn || !links) return;

    btn.addEventListener('click', function () {
      links.classList.toggle('open');
    });

    links.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        links.classList.remove('open');
      });
    });
  }

  
  function initActiveNav() {
    var path = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(function (link) {
      var href = link.getAttribute('href');
      if (href === path) {
        link.classList.add('active');
      }
    });
  }

  
  function initCounters() {
    var counters = document.querySelectorAll('.counter');
    if (counters.length === 0) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var counter = entry.target;
          var target = parseInt(counter.getAttribute('data-target'), 10);
          if (isNaN(target)) return;
          var current = 0;
          var increment = Math.ceil(target / 50);
          var interval = setInterval(function () {
            current += increment;
            if (current >= target) {
              current = target;
              clearInterval(interval);
            }
            counter.textContent = current;
          }, 20);
          observer.unobserve(counter);
        }
      });
    }, { threshold: 0.5 });

    counters.forEach(function (c) {
      observer.observe(c);
    });
  }

  
  function initDemoCycle() {
    
    var demoLetter = document.getElementById('demoLetter');
    var hasSignGrid = document.querySelector('.sign-grid');
    if (!demoLetter || hasSignGrid) return;

    var letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'L', 'O', 'Y'];
    var confs = [97, 96, 98, 95, 94, 97, 96, 93, 95, 98, 92, 97];
    var sounds = ['"A"', '"B"', '"C"', '"D"', '"E"', '"F"', '"G"', '"H"', '"I"', '"L"', '"O"', '"Y"'];
    var idx = 0;

    setInterval(function () {
      demoLetter.textContent = letters[idx];
      var speechEl = document.getElementById('demoSpeech');
      if (speechEl) speechEl.textContent = sounds[idx];
      var confDiv = demoLetter.closest('.prediction-box').querySelector('.confidence');
      if (confDiv) {
        confDiv.textContent = 'Confidence: ' + confs[idx] + '%';
      }
      idx = (idx + 1) % letters.length;
    }, 1400);
  }

  
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      anchor.addEventListener('click', function (e) {
        var href = this.getAttribute('href');
        if (!href || href === '#' || href.indexOf('#') !== 0) return;
        e.preventDefault();
        var target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  
  function initHeroTilt() {
    var heroVisual = document.getElementById('heroVisual');
    if (!heroVisual) return;

    var ticking = false;
    heroVisual.addEventListener('mousemove', function (e) {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          var rect = heroVisual.getBoundingClientRect();
          var x = (e.clientX - rect.left) / rect.width - 0.5;
          var y = (e.clientY - rect.top) / rect.height - 0.5;
          heroVisual.style.transform =
            'perspective(1000px) rotateY(' + (x * 15) + 'deg) rotateX(' + (-y * 15) + 'deg) translateZ(10px)';
          ticking = false;
        });
        ticking = true;
      }
    });

    heroVisual.addEventListener('mouseleave', function () {
      heroVisual.style.transform = 'perspective(1000px) rotateY(0deg) rotateX(0deg) translateZ(0)';
    });
  }

  
  function initBackToTop() {
    var btn = document.getElementById('back-to-top');
    if (!btn) return;

    window.addEventListener('scroll', function () {
      if (window.scrollY > 400) {
        btn.classList.add('visible');
      } else {
        btn.classList.remove('visible');
      }
    });

    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  
  function initDownloadButtons() {
    var btnContainer = document.getElementById('downloadButtons');
    var versionEl = document.getElementById('releaseVersion');
    if (!btnContainer) return;

    function applyRelease(tag, assets) {
      if (versionEl) versionEl.textContent = tag;
      var btns = btnContainer.querySelectorAll('.download-btn');
      btns.forEach(function (b) {
        var os = b.getAttribute('data-os');
        var assetNames = os === 'windows'
          ? ['AI-Sign-Bridge-Windows.zip', 'AI-Sign-Bridge.exe']
          : ['AI-Sign-Bridge-macOS.dmg'];
        var asset = null;
        for (var i = 0; i < assetNames.length; i++) {
          asset = assets.find(function (a) { return a.name === assetNames[i]; });
          if (asset) break;
        }
        if (asset) {
          b.href = asset.browser_download_url;
          b.setAttribute('target', '_blank');
        }
      });
    }

    function applyLegacy(data) {
      if (versionEl) versionEl.textContent = data.latest_version;
      var btns = btnContainer.querySelectorAll('.download-btn');
      btns.forEach(function (b) {
        var os = b.getAttribute('data-os');
        if (data.download_urls && data.download_urls[os]) {
          b.href = data.download_urls[os];
          b.setAttribute('target', '_blank');
        }
      });
    }

    fetch('https://api.github.com/repos/katrate/AISignBridge/releases/latest')
      .then(function (r) {
        if (!r.ok) throw new Error('GitHub API failed');
        return r.json();
      })
      .then(function (data) {
        applyRelease(data.tag_name, data.assets);
      })
      .catch(function () {
        fetch('release-data.json?' + Date.now())
          .then(function (r) { return r.json(); })
          .then(applyLegacy)
          .catch(function () {
            if (versionEl) versionEl.textContent = '—';
          });
      });
  }

  
  function initDemoInteractive() {
    var cells = document.querySelectorAll('.sign-cell');
    if (cells.length === 0) return;
    
    if (document.querySelector('script[data-demo-inline]')) return;

    var liveLetter = document.getElementById('liveLetter');
    var liveSpeech = document.getElementById('liveSpeech');
    var liveConf = document.getElementById('liveConfidence');
    var historyBar = document.getElementById('historyBar');
    var sessionCount = document.getElementById('sessionCount');
    var count = parseInt(sessionCount ? sessionCount.textContent : '0', 10) || 0;

    cells.forEach(function (cell) {
      cell.addEventListener('click', function () {
        var char = this.dataset.char;
        cells.forEach(function (c) { c.classList.remove('active'); });
        this.classList.add('active');

        var conf = Math.floor(Math.random() * 7 + 92);
        if (liveLetter) liveLetter.textContent = char;
        if (liveSpeech) liveSpeech.textContent = '"' + char + '"';
        if (liveConf) liveConf.textContent = 'Confidence: ' + conf + '%';
        count++;
        if (sessionCount) sessionCount.textContent = count;

        if (historyBar) {
          var placeholder = historyBar.querySelector('span[style]');
          if (placeholder && historyBar.children.length === 1) historyBar.innerHTML = '';
          var tag = document.createElement('span');
          tag.className = 'tag';
          tag.textContent = char;
          historyBar.appendChild(tag);
          while (historyBar.children.length > 12) {
            historyBar.removeChild(historyBar.firstChild);
          }
        }
      });
    });
  }

  
  function initParallax() {
    var parallaxElements = document.querySelectorAll('.parallax');
    if (parallaxElements.length === 0) return;

    window.addEventListener('scroll', function () {
      var scrollY = window.scrollY;
      parallaxElements.forEach(function (el) {
        var speed = parseFloat(el.getAttribute('data-speed')) || 0.5;
        el.style.transform = 'translateY(' + (scrollY * speed * 0.1) + 'px)';
      });
    });
  }

  
  function initThemeToggle() {
    var btn = document.getElementById('themeToggle');
    if (!btn) return;

    function setIcon(name) {
      if (typeof lucide !== 'undefined' && typeof lucide.createIcons === 'function') {
        btn.innerHTML = '<i data-lucide="' + name + '"></i>';
        lucide.createIcons();
      }
    }

    var saved = localStorage.getItem('ai-sign-bridge-theme');
    if (saved === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
      setIcon('sun');
    }

    btn.addEventListener('click', function () {
      var html = document.documentElement;
      var isLight = html.getAttribute('data-theme') === 'light';
      if (isLight) {
        html.removeAttribute('data-theme');
        localStorage.setItem('ai-sign-bridge-theme', 'dark');
        setIcon('moon');
      } else {
        html.setAttribute('data-theme', 'light');
        localStorage.setItem('ai-sign-bridge-theme', 'light');
        setIcon('sun');
      }
    });
  }

  
  function initLucideIcons() {
    if (typeof lucide !== 'undefined' && typeof lucide.createIcons === 'function') {
      lucide.createIcons();
    }
  }

  
  document.addEventListener('DOMContentLoaded', function () {
    initThreeScene();
    initScrollProgress();
    initNavbar();
    initMobileMenu();
    initActiveNav();
    initScrollReveal();
    initCounters();
    initDemoCycle();
    initSmoothScroll();
    initHeroTilt();
    initBackToTop();
    initDownloadButtons();
    initDemoInteractive();
    initParallax();
    initThemeToggle();

    
    setTimeout(initLucideIcons, 100);
  });

})();
