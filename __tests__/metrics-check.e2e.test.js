// Headless E2E check for examples/metrics-check using Puppeteer
// Usage:
//   1) npm i -D puppeteer
//   2) npm run test:e2e

import http from 'http';
import { promises as fsp } from 'fs';
import path from 'path';
import url from 'url';

// Only run when explicitly requested
const RUN_E2E = process.env.RUN_E2E === '1';

// Very small static file server for the repo root
function startStaticServer(rootDir) {
  const mime = (p) => {
    const ext = path.extname(p).toLowerCase();
    switch (ext) {
      case '.html': return 'text/html; charset=utf-8';
      case '.js': return 'text/javascript; charset=utf-8';
      case '.css': return 'text/css; charset=utf-8';
      case '.json': return 'application/json; charset=utf-8';
      case '.woff2': return 'font/woff2';
      case '.ttf': return 'font/ttf';
      case '.woff': return 'font/woff';
      case '.txt': return 'text/plain; charset=utf-8';
      default: return 'application/octet-stream';
    }
  };

  const server = http.createServer(async (req, res) => {
    try {
      const reqUrl = new URL(req.url, 'http://localhost');
      let rel = decodeURIComponent(reqUrl.pathname);
      if (rel === '/' || rel === '') {
        rel = '/examples/metrics-check/index.html';
      }
      // Prevent path traversal
      const safePath = path.normalize(rel).replace(/^\/+/, '');
      const filePath = path.join(rootDir, safePath);

      const data = await fsp.readFile(filePath);
      res.writeHead(200, { 'Content-Type': mime(filePath) });
      res.end(data);
    } catch (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found');
    }
  });

  return new Promise((resolve) => {
    server.listen(0, () => {
      const addr = server.address();
      resolve({ server, port: addr.port });
    });
  });
}

const repoRoot = path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), '..');

(RUN_E2E ? describe : describe.skip)('examples/metrics-check (headless)', () => {
  let server, port;

  beforeAll(async () => {
    const s = await startStaticServer(repoRoot);
    server = s.server; port = s.port;
  });

  afterAll(async () => {
    if (server) await new Promise((r) => server.close(r));
  });

  test('renders and measures without errors', async () => {
    let puppeteer;
    try {
      puppeteer = await import('puppeteer');
    } catch (e) {
      console.warn('Puppeteer not installed. Skipping E2E.');
      return; // effectively skip
    }

    const browser = await puppeteer.launch({
      headless: true,
      args: process.env.CI ? ['--no-sandbox', '--disable-setuid-sandbox'] : []
    });
    try {
      const page = await browser.newPage();
      await page.goto(`http://127.0.0.1:${port}/examples/metrics-check/index.html`, { waitUntil: 'load' });

      // Ensure page loaded and buttons exist
      await page.waitForSelector('#btnLoad');
      await page.click('#btnLoad');
      // Wait until the page logs the font loaded message
      await page.waitForFunction(() => {
        const el = document.getElementById('result');
        return !!(el && el.textContent && el.textContent.includes('Font loaded'));
      });

      await page.click('#btnMeasure');
      // Wait until a measure+render JSON log appears
      await page.waitForFunction(() => {
        const el = document.getElementById('result');
        if (!el || !el.textContent) return false;
        return /"context"\s*:\s*"measure\+render"/.test(el.textContent);
      });

      // Wait until the sample element renders with width > 0
      await page.waitForFunction(() => {
        const el = document.getElementById('sampleWith');
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return !!el.textContent && r.width > 0;
      });

      // Compute measurement in-page to avoid parsing multiline JSON logs
      const measure = await page.evaluate(() => {
        const sampleWith = document.getElementById('sampleWith');
        const size = document.getElementById('fontSize').value;
        const family = document.getElementById('fontFamily').value;
        const text = sampleWith.textContent || '';
        const fontCSS = `${size} ${family}`;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.font = fontCSS;
        const m = ctx.measureText(text);
        const wCanvas = m.width;
        let hCanvas;
        if (typeof m.actualBoundingBoxAscent === 'number' && typeof m.actualBoundingBoxDescent === 'number') {
          hCanvas = m.actualBoundingBoxAscent + m.actualBoundingBoxDescent;
        } else {
          const msize = /(^|\s)(\d+(?:\.\d+)?)(px)/i.exec(fontCSS);
          hCanvas = msize ? parseFloat(msize[2]) : 0;
        }

        const rect = sampleWith.getBoundingClientRect();
        return { wCanvas, hCanvas, wRender: rect.width, hRender: rect.height };
      });

      expect(measure).not.toBeNull();
      expect(typeof measure.wCanvas).toBe('number');
      expect(typeof measure.wRender).toBe('number');
      expect(measure.wCanvas).toBeGreaterThan(0);
      expect(measure.wRender).toBeGreaterThan(0);

      // Tolerance check: DOM and Canvas widths are reasonably close
      const wDiff = Math.abs(measure.wRender - measure.wCanvas);
      expect(wDiff).toBeLessThan(1); // px tolerance
    } finally {
      await browser.close();
    }
  }, 20000);
});
