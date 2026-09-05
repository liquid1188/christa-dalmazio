import { chromium } from 'playwright';
const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1280,height:900}});
await p.goto('http://localhost:8765/press-kit/'); await p.addStyleTag({content:'.reveal{opacity:1!important;transform:none!important}'});
const el = await p.$('.photo-grid'); await el.screenshot({path:'/tmp/photos.png'});
await p.setViewportSize({width:390,height:800}); await p.goto('http://localhost:8765/upcoming/'); await p.addStyleTag({content:'.reveal{opacity:1!important;transform:none!important}'});
const u = await p.$('.up-list'); await u.screenshot({path:'/tmp/up.png'});
await b.close();
