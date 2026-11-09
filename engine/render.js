// Render one HTML file to PNG with the pre-installed Playwright Chromium.
// Usage: node engine/render.js <in.html> <out.png> <width> <height>
// Exits 3 if any element marked .fit overflows (text too long), so the caller
// can shorten the copy instead of publishing a clipped image.
const { chromium } = require('playwright');

(async () => {
  const [inPath, outPath, w, h] = process.argv.slice(2);
  const width = parseInt(w, 10), height = parseInt(h, 10);
  let browser;
  try {
    browser = await chromium.launch();
  } catch (e) {
    browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  }
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 });
  await page.goto('file://' + inPath);
  await page.evaluate(() => document.fonts.ready);
  const overflow = await page.evaluate(() =>
    [...document.querySelectorAll('.fit')]
      .filter(el => el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1)
      .map(el => el.dataset.name || el.className));
  if (overflow.length) {
    console.error('OVERFLOW: ' + overflow.join(', '));
    await browser.close();
    process.exit(3);
  }
  await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width, height } });
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
