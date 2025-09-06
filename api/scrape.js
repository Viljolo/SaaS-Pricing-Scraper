let chromium, puppeteer;
try {
  chromium = require('@sparticuz/chromium');
  puppeteer = require('puppeteer-core');
} catch (err) {
  console.log('Puppeteer dependencies not available:', err.message);
}

function buildCorsHeaders(originHeader) {
  const allowedOriginsEnv = process.env.CORS_ORIGINS || '*';
  const allowedOrigins = allowedOriginsEnv.split(',').map(o => o.trim()).filter(Boolean);
  const allowAll = allowedOrigins.includes('*');
  const origin = originHeader || '';
  const allowOriginHeader = allowAll ? '*' : (allowedOrigins.includes(origin) ? origin : allowedOrigins[0] || '*');
  return {
    'Access-Control-Allow-Origin': allowOriginHeader,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
  };
}

function normalizeUrl(inputUrl) {
  try {
    if (!inputUrl) return '';
    if (!/^https?:\/\//i.test(inputUrl)) {
      return `https://${inputUrl}`;
    }
    return inputUrl;
  } catch (_) {
    return '';
  }
}

function inferPricingModel(text) {
  const lower = text.toLowerCase();
  if (/contact\s+(sales|us)|talk\s+to\s+sales|request\s+a\s+quote|custom\s+pricing/.test(lower)) return 'Custom';
  if (/(per\s*user|\/user|per\s*seat|\/seat)/.test(lower)) return 'Per-User';
  if (/(per\s*(api|gb|request|usage|unit)|\busage\b|pay\s+as\s+you\s+go)/.test(lower)) return 'Usage-Based';
  if (/(free|\$?0\b)/.test(lower)) return 'Freemium';
  return 'Tiered';
}

function parseBillingCycle(text) {
  const lower = text.toLowerCase();
  if (/month|mo\b/.test(lower)) return 'monthly';
  if (/year|annual|yr\b/.test(lower)) return 'annually';
  if (/(per\s*user|\/user|per\s*seat|\/seat)/.test(lower)) return 'per user';
  return 'N/A';
}

export default async function handler(req, res) {
  const corsHeaders = buildCorsHeaders(req.headers.origin);

  // CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).set(corsHeaders).send('');
  }

  if (req.method !== 'POST') {
    return res.status(405).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ error: 'Method not allowed' });
  }

  // API key auth
  const apiKeyHeader = req.headers['x-api-key'];
  const expectedKey = process.env.SCRAPER_API_KEY || '';
  if (!expectedKey || apiKeyHeader !== expectedKey) {
    return res.status(401).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ error: 'Unauthorized' });
  }

  try {
    const { url } = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
    const targetUrl = normalizeUrl(url);
    if (!targetUrl) {
      return res.status(400).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ error: 'Invalid or missing url' });
    }

    // Check if puppeteer is available
    if (!chromium || !puppeteer) {
      return res.status(500).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ 
        error: 'Puppeteer dependencies not available. Try /api/scrape-simple for basic scraping.' 
      });
    }

    // Configure Chromium for serverless
    chromium.setHeadlessMode = true;
    chromium.setGraphicsMode = false;

    const launchOptions = {
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath(),
      headless: chromium.headless,
      ignoreHTTPSErrors: true,
    };

    const browser = await puppeteer.launch(launchOptions);
    try {
      const page = await browser.newPage();
      await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36');
      await page.setRequestInterception(true);
      page.on('request', (request) => {
        const resourceType = request.resourceType();
        if (['image', 'media', 'font'].includes(resourceType)) {
          request.abort();
        } else {
          request.continue();
        }
      });

      // Navigate with tight timeout to fit serverless limits
      try {
        await page.goto(targetUrl, { waitUntil: ['domcontentloaded', 'networkidle2'], timeout: 8000 });
      } catch (_) {
        // Fallback to at least DOM ready
        try { await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout: 8000 }); } catch (_) {}
      }

      // Small grace period for late content
      await page.waitForTimeout(300);

      const results = await Promise.race([
        page.evaluate(() => {
          function getText(el) { return (el && el.textContent || '').replace(/\s+/g, ' ').trim(); }
          const currencyRe = /(?:\$|€|£)\s?\d{1,3}(?:[\,\.]\d{3})*(?:[\.,]\d{2})?|\bfree\b|contact\s+(?:sales|us)|request\s+a\s+quote/i;

          // Find nodes with price-like text
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
          const priceNodes = [];
          while (walker.nextNode()) {
            const node = walker.currentNode;
            const text = getText(node);
            if (!text) continue;
            if (currencyRe.test(text)) {
              priceNodes.push(node);
            }
            if (priceNodes.length > 120) break; // cap for performance
          }

          // For each price node, find a reasonable plan card ancestor
          function findCard(node) {
            let cur = node;
            let depth = 0;
            while (cur && depth < 6) {
              const text = getText(cur).toLowerCase();
              const hasList = cur.querySelectorAll('li').length >= 2;
              const hasHeading = cur.querySelector('h1,h2,h3,h4,h5,h6,[class*="plan" i],[class*="tier" i],[class*="title" i]');
              const containsMultiplePrices = (text.match(/\$|€|£/g) || []).length <= 6; // avoid grabbing whole page
              const hasColumns = getComputedStyle(cur).display.includes('grid') || getComputedStyle(cur).display.includes('flex');
              if ((hasHeading || hasList || hasColumns) && containsMultiplePrices) {
                return cur;
              }
              cur = cur.parentElement;
              depth += 1;
            }
            return node;
          }

          const cards = new Set();
          const planCards = [];
          for (const pn of priceNodes) {
            const card = findCard(pn);
            if (!card) continue;
            if (cards.has(card)) continue;
            cards.add(card);
            planCards.push(card);
            if (planCards.length > 12) break; // cap
          }

          function extractFromCard(card) {
            const text = getText(card);
            // Price
            let price = '';
            const priceEl = card.querySelector('[class*="price" i], [data-test*="price" i]');
            price = priceEl ? getText(priceEl) : '';
            if (!price || !/(\$|€|£|free|contact|quote)/i.test(price)) {
              const m = text.match(currencyRe);
              if (m) price = m[0];
            }

            // Plan name
            let planName = '';
            const heading = card.querySelector('h1,h2,h3,h4,h5,h6,[class*="plan" i],[class*="tier" i],[class*="name" i],[class*="title" i]');
            if (heading) planName = getText(heading);
            if (!planName) {
              // Try previous sibling heading
              let prev = card.previousElementSibling;
              if (prev) {
                const h = prev.querySelector('h1,h2,h3,h4,h5,h6');
                if (h) planName = getText(h);
              }
            }

            // Features
            let features = Array.from(card.querySelectorAll('li'))
              .map(li => getText(li))
              .filter(Boolean)
              .slice(0, 20);

            // Billing cycle (from card text or price)
            let billingText = '';
            const cycleCandidates = [
              card.querySelector('[class*="billing" i]'),
              card.querySelector('[class*="cycle" i]'),
              card.querySelector('[class*="period" i]'),
              card.querySelector('[class*="per" i]')
            ].filter(Boolean);
            if (cycleCandidates.length) billingText = getText(cycleCandidates[0]);
            const billing_cycle = (() => {
              const t = (billingText || price || text).toLowerCase();
              if (/month|mo\b/.test(t)) return 'monthly';
              if (/year|annual|yr\b/.test(t)) return 'annually';
              if (/(per\s*user|\/user|per\s*seat|\/seat)/.test(t)) return 'per user';
              return 'N/A';
            })();

            // Pricing model
            const pricing_model = (() => {
              const t = (text + ' ' + price).toLowerCase();
              if (/contact\s+(sales|us)|talk\s+to\s+sales|request\s+a\s+quote|custom\s+pricing/.test(t)) return 'Custom';
              if (/(per\s*user|\/user|per\s*seat|\/seat)/.test(t)) return 'Per-User';
              if (/(per\s*(api|gb|request|usage|unit)|\busage\b|pay\s+as\s+you\s+go)/.test(t)) return 'Usage-Based';
              if (/(^|\s)(free|\$?0\b)/.test(t)) return 'Freemium';
              return 'Tiered';
            })();

            return { plan_name: planName || '', price: price || '', pricing_model, features, billing_cycle };
          }

          const extracted = planCards.map(extractFromCard)
            .filter(p => p.price || p.plan_name)
            .slice(0, 8);

          // Deduplicate by plan name + price
          const seen = new Set();
          const unique = [];
          for (const p of extracted) {
            const key = (p.plan_name + '|' + p.price).toLowerCase();
            if (seen.has(key)) continue;
            seen.add(key);
            unique.push(p);
          }

          return unique;
        }),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Extraction timeout')), 2500))
      ]);

      return res.status(200).set({ 'Content-Type': 'application/json', ...corsHeaders }).json(Array.isArray(results) ? results : []);
    } finally {
      await browser.close().catch(() => {});
    }
  } catch (err) {
    return res.status(500).set({ 'Content-Type': 'application/json', ...corsHeaders }).json({ error: String(err && err.message || err) });
  }
}

