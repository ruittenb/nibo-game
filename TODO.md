
 - fix landing gear of ship

 - central pick up icon in nav-panel

 - animated items still below darkness mask: plan 'flying-coins' (css stacking context problem)

 - burn disease with torch?

 - use more :is() selectors






serviceworker

// sw.js
self.addEventListener('fetch', (e) => e.respondWith(fetch(e.request)));

// In je main JS
navigator.serviceWorker?.register('/sw.js');

