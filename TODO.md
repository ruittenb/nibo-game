
 - fix landing gear of ship

 - burn disease with torch?
 - gold eating NPC / requiring payment
 - fly item to in-game location when applied

 - color arrow purple when it leads to death?
 - pick up objects in center of nav-panel?

 - start with some boxes already checked?


S6: Contains an important part for repairs.
    But requires a special radioactivity suit.

S7: Then on S7 I love the idea of an ancient alien temple with a guardian that wants payment.
    Contains the radiation shield.
    What kinds of interesting obstacles could we have here? moving platforms? Falling blocks?

--------------------------------------------------------------------------------
javascript:void(['pos-13','level-5','title-screen-toggle'].forEach(id=>document.getElementById(id).checked=true),['torch-pickup','loot-S1-L0-P3-pickup','loot-S1-L1-P4-pickup','loot-S1-L3-P5-pickup','loot-S1-L2-P1-pickup','loot-S1-L4-P2-pickup','loot-S2-L5-P8-pickup','loot-S2-L6-P11-pickup','loot-S2-L7-P7-pickup','loot-S2-L8-P9-pickup','loot-S2-L9-P10-pickup','loot-S3-L5-P15-pickup','loot-S3-L5-P18-pickup','loot-S3-L8-P18-pickup','loot-S3-L9-P14-pickup','loot-S4-L3-P7-pickup','loot-S4-L3-P8-pickup','loot-S4-L3-P12-pickup','loot-S4-L1-P10-pickup','loot-S4-L0-P9-pickup','loot-S5-L3-P13-pickup','loot-S5-L2-P17-pickup','loot-S5-L0-P18-pickup','loot-S6-L9-P24-pickup','loot-S6-L5-P24-pickup'].forEach(id=>document.getElementById(id).checked=true))
--------------------------------------------------------------------------------
 - serviceworker?
    // sw.js
    self.addEventListener('fetch', (e) => e.respondWith(fetch(e.request)));
    // main.js
    navigator.serviceWorker?.register('/sw.js');

