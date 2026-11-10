// Phones and tablets: runs before anything paints. Tags <html class="touch"> and zooms the page out on small screens,
// so the menus and HUD (drawn for a 640 px tall window) fit a phone in landscape. Desktop never gets past the first line.
// ?touch=1 forces it on (testing on a desktop), ?touch=0 forces it off.
(function () {
  var q = /[?&]touch=([01])/.exec(location.search);
  var coarse = false;
  try { coarse = navigator.maxTouchPoints > 0 && matchMedia('(pointer: coarse)').matches && !matchMedia('(any-pointer: fine)').matches; } catch (e) { /* old browser */ }
  if (window.jf) coarse = false; // the desktop exe
  if (q ? q[1] !== '1' : !coarse) return;
  var root = document.documentElement, meta = document.querySelector('meta[name=viewport]');
  root.classList.add('touch');
  var MINH = 640; // the UI's design height: shorter screens zoom out to this
  function fit() {
    // screen.* is in device px whatever the zoom is (iOS never swaps them on rotate: take short/long ourselves)
    var a = screen.width, b = screen.height, land = true;
    try { land = matchMedia('(orientation: landscape)').matches; } catch (e) { /* assume landscape */ }
    var short = Math.min(a, b), long = Math.max(a, b);
    var h = land ? short : long;
    var s = Math.min(1, Math.max(0.3, h / MINH));
    if (!land) s = Math.min(1, Math.max(0.3, short / 420)); // portrait only shows the "turn your phone" card
    s = Math.round(s * 1000) / 1000;
    window.JF_TOUCH = { on: true, scale: s };
    root.style.setProperty('--tu', String(1 / s)); // 1 finger-px in page px: touch buttons are sized with it
    if (meta) meta.setAttribute('content', 'width=device-width, initial-scale=' + s + ', minimum-scale=' + s + ', maximum-scale=' + s + ', user-scalable=no, viewport-fit=cover');
    root.classList.toggle('portrait', !land);
  }
  fit();
  addEventListener('orientationchange', function () { setTimeout(fit, 60); });
  try { matchMedia('(orientation: landscape)').addEventListener('change', fit); } catch (e) { /* old safari: orientationchange covers it */ }
})();
