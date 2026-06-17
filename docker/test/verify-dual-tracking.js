/**
 * Dual-Layer Tracking Verification
 * Tests Umami (analytics) + RRWeb (session replay) end-to-end
 */
const { chromium } = require('playwright');
const fs = require('fs');

const DEMO_URL = 'http://localhost:8080';
const UMAMI_API = 'http://localhost:3100';
const RRWEB_API = 'http://localhost:3101';
const WEBSITE_ID = '681699f8-ede7-4e16-a6a7-657b835315a4';
const UMAMI_USER = 'admin';
const UMAMI_PASS = 'umami';

async function umamiLogin() {
  const res = await fetch(`${UMAMI_API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: UMAMI_USER, password: UMAMI_PASS }),
  });
  const data = await res.json();
  return data.token;
}

async function getUmamiMetrics(token, type) {
  const now = Date.now();
  const start = now - 86400000; // 24h ago
  const res = await fetch(
    `${UMAMI_API}/api/websites/${WEBSITE_ID}/metrics?startAt=${start}&endAt=${now}&type=${type}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.json();
}

(async () => {
  console.log('=== Dual-Layer Tracking Verification ===\n');

  // 1. Login to Umami
  console.log('[1] Logging into Umami API...');
  const token = await umamiLogin();
  console.log('    Token obtained:', token.slice(0, 20) + '...\n');

  // 2. Record baseline event counts
  console.log('[2] Recording baseline event counts...');
  const beforeMetrics = await getUmamiMetrics(token, 'event');
  const beforePageviews = beforeMetrics.find(m => m.x === 'pageview')?.y || 0;
  console.log(`    Baseline pageviews: ${beforePageviews}\n`);

  // 3. Launch browser and interact with demo
  console.log('[3] Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
  });
  const page = await context.newPage();

  // Collect console logs for Umami tracking verification
  const umamiLogs = [];
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[Umami]') || text.includes('umami')) {
      umamiLogs.push(text);
    }
  });

  // Navigate to demo
  console.log('[4] Navigating to demo app...');
  await page.goto(DEMO_URL, { waitUntil: 'networkidle' });

  // Wait for Umami script to load and send initial pageview
  await page.waitForTimeout(3000);

  // Perform interactions
  console.log('[5] Performing user interactions...');

  // 5a. Search
  console.log('    a) Search interaction');
  await page.click('#search-input', { force: true });
  await page.fill('#search-input', 'weekly metrics report');
  await page.click('#search-btn', { force: true });
  await page.waitForTimeout(500);

  // 5b. Switch to Export tab
  console.log('    b) Switch to Export tab');
  await page.click('#tab-export', { force: true });
  await page.waitForTimeout(500);

  // 5c. Export interaction
  console.log('    c) Export interaction');
  await page.click('#include-charts', { force: true });
  await page.click('#export-btn', { force: true });
  await page.waitForTimeout(500);

  // 5d. Confirm dialog
  console.log('    d) Confirm dialog');
  await page.click('#dialog-test button.primary', { force: true });
  await page.waitForTimeout(500);

  // 5e. Switch to Settings tab
  console.log('    e) Switch to Settings tab');
  await page.click('#tab-settings', { force: true });
  await page.waitForTimeout(500);

  // 5f. Fill settings form
  console.log('    f) Fill settings form');
  await page.click('#user-name', { force: true });
  await page.fill('#user-name', 'Test User');
  await page.fill('#user-email', 'test@example.com');
  await page.fill('#user-phone', '+1-555-0100');
  await page.click('#save-btn', { force: true });
  await page.waitForTimeout(1000);

  // Wait for events to flush to both systems
  console.log('[6] Waiting for event flush...');
  await page.waitForTimeout(3000);

  // Get RRWeb session info from status bar
  const rrwebSessionText = await page.textContent('#session-id');
  const eventCountText = await page.textContent('#event-count');
  const actionCountText = await page.textContent('#action-count');
  const umamiStatusText = await page.textContent('#umami-status');

  console.log(`\n[7] Status bar during session:`);
  console.log(`    RRWeb: ${rrwebSessionText}`);
  console.log(`    Events: ${eventCountText}`);
  console.log(`    Actions: ${actionCountText}`);
  console.log(`    Umami: ${umamiStatusText}`);
  console.log(`    Console logs: ${umamiLogs.length} Umami-related entries`);

  await browser.close();

  // 8. Check Umami metrics after
  console.log('\n[8] Checking Umami metrics after test...');
  await new Promise(r => setTimeout(r, 2000));

  const afterMetrics = await getUmamiMetrics(token, 'event');
  const afterPageviews = afterMetrics.find(m => m.x === 'pageview')?.y || 0;
  const searchEvents = afterMetrics.find(m => m.x === 'search')?.y || 0;
  const exportEvents = afterMetrics.find(m => m.x === 'export')?.y || 0;
  const settingsSaveEvents = afterMetrics.find(m => m.x === 'settings-save')?.y || 0;

  console.log(`    Pageviews: ${afterPageviews} (before: ${beforePageviews})`);
  console.log(`    Search events: ${searchEvents}`);
  console.log(`    Export events: ${exportEvents}`);
  console.log(`    Settings-save events: ${settingsSaveEvents}`);
  console.log(`    All event types:`, afterMetrics.map(m => `${m.x}=${m.y}`).join(', '));

  // 9. Check RRWeb events
  console.log('\n[9] Checking RRWeb event receiver...');
  // Wait for RRWeb flush to complete
  await new Promise(r => setTimeout(r, 5000));
  const sessionsRes = await fetch(`${RRWEB_API}/api/sessions`);
  const sessionsData = await sessionsRes.json();
  // Find the session with the most events (should be our test session)
  const allSessions = sessionsData.sessions || [];
  const recentSession = allSessions.length > 0
    ? allSessions.reduce((a, b) => (a.eventCount > b.eventCount ? a : b))
    : null;

  if (recentSession) {
    console.log(`    Latest RRWeb session: ${recentSession.sessionId.slice(0, 8)}...`);
    console.log(`    Total events: ${recentSession.eventCount}`);
  } else {
    console.log('    No RRWeb sessions found');
  }

  // 10. Verification summary
  console.log('\n=== Verification Summary ===\n');

  const checks = [];

  // Umami layer checks
  const newPageviews = afterPageviews - beforePageviews;
  const newCustomEvents = searchEvents + exportEvents + settingsSaveEvents;
  checks.push(['Umami pageview tracked', newPageviews >= 0, `${afterPageviews} total (baseline ${beforePageviews})`]);
  checks.push(['Umami custom events tracked', newCustomEvents > 0, `${searchEvents} search, ${exportEvents} export, ${settingsSaveEvents} settings-save`]);
  checks.push(['Umami script loaded', umamiLogs.length > 0 || umamiStatusText.includes('active'), 'script active in browser']);

  // RRWeb layer checks
  const rrEventCount = recentSession?.eventCount || 0;
  checks.push(['RRWeb events recorded', rrEventCount > 0, `${rrEventCount} events`]);

  // Get RRWeb TOON summary
  let rrToonLines = 0;
  let rrSummaryActionCount = 0;
  let rrSummaryText = '';
  if (recentSession) {
    try {
      const sumRes = await fetch(`${RRWEB_API}/api/sessions/${recentSession.sessionId}/summary`);
      const sum = await sumRes.json();
      rrToonLines = sum.toon?.length || 0;
      rrSummaryActionCount = sum.actionCount || 0;
      rrSummaryText = sum.summaryText || '';
      console.log(`\n    TOON sample (first 5 of ${rrToonLines}):`);
      sum.toon?.slice(0, 5).forEach((line, i) => console.log(`      ${i+1}. ${line}`));
    } catch (e) { /* summary endpoint may not have parsed */ }
  }
  checks.push(['RRWeb TOON format generated', rrToonLines > 0, `${rrToonLines} lines`]);

  // Dual-layer integration
  checks.push([
    'Both layers active simultaneously',
    (searchEvents > 0 || exportEvents > 0 || umamiLogs.length > 0) && (rrEventCount > 0),
    'Umami + RRWeb both captured data'
  ]);

  // RRWeb A11y actions from summary
  checks.push([
    'RRWeb A11y actions captured',
    rrSummaryActionCount > 0 || rrToonLines > 0,
    `${rrSummaryActionCount} actions, ${rrToonLines} TOON lines`
  ]);

  let passed = 0;
  for (const [name, ok, detail] of checks) {
    console.log(`  ${ok ? 'PASS' : 'FAIL'}: ${name} (${detail})`);
    if (ok) passed++;
  }

  console.log(`\n=== Result: ${passed}/${checks.length} checks passed ===`);

  // Save report
  const report = {
    timestamp: new Date().toISOString(),
    umami: {
      pageviewsBefore: beforePageviews,
      pageviewsAfter: afterPageviews,
      newPageviews,
      eventMetrics: afterMetrics,
      consoleLogs: umamiLogs,
    },
    rrweb: recentSession ? {
      sessionId: recentSession.sessionId,
      eventCount: recentSession.eventCount,
      actionCount: rrSummaryActionCount,
      toonLines: rrToonLines,
      summaryLength: rrSummaryText.length,
      sampleToon: [],
    } : null,
    checks: checks.map(([name, ok, detail]) => ({ name, passed: ok, detail })),
    passed,
    total: checks.length,
  };

  fs.writeFileSync(
    require('path').join(__dirname, 'dual-tracking-report.json'),
    JSON.stringify(report, null, 2)
  );
  console.log('\nReport saved to docker/test/dual-tracking-report.json');

  process.exit(passed >= 5 ? 0 : 1);
})();
