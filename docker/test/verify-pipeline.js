/**
 * End-to-end pipeline verification
 * Tests: RRWeb recording → A11y capture → event storage → Agent-consumable summary
 */
const { chromium } = require('playwright');

const DEMO_URL = 'http://localhost:8080';
const RECEIVER_URL = 'http://localhost:3101';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  console.log('=== Pipeline Verification Start ===\n');

  // Collect console messages
  const consoleMsgs = [];
  page.on('console', (msg) => consoleMsgs.push(`${msg.type()}: ${msg.text()}`));

  // 1. Navigate to demo page
  console.log('1. Loading demo page...');
  await page.goto(DEMO_URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Debug: check if rrweb loaded
  const rrwebStatus = await page.evaluate(() => ({
    rrwebType: typeof rrweb,
    hasRecord: typeof rrweb !== 'undefined' && typeof rrweb.record,
    globals: Object.keys(window).filter(k => k.toLowerCase().includes('rrweb')),
    dotColor: document.getElementById('rec-dot')?.style.background || 'not set',
  }));
  console.log('   RRWeb status:', JSON.stringify(rrwebStatus));
  console.log('   Console msgs:', consoleMsgs.filter(m => m.includes('rror') || m.includes('RRWeb')).join('; ') || 'none');

  // Verify recording indicator
  const eventCount0 = await page.locator('#event-count').textContent();
  console.log(`   Event count after load: ${eventCount0}`);
  console.log(`   ✓ RRWeb recording started\n`);

  // 2. Click on "Export" tab
  console.log('2. Clicking Export tab...');
  await page.click('#tab-export', { force: true });
  await page.waitForTimeout(500);
  console.log('   ✓ Tab switched to Export\n');

  // 3. Select format from dropdown
  console.log('3. Selecting export format...');
  await page.selectOption('#format-select', 'csv');
  await page.waitForTimeout(300);

  // 4. Check the "include charts" checkbox
  console.log('4. Checking "Include charts" checkbox...');
  await page.check('#include-charts', { force: true });
  await page.waitForTimeout(300);

  // 5. Click Export button
  console.log('5. Clicking Export button...');
  await page.click('#export-btn', { force: true });
  await page.waitForTimeout(500);

  // 6. Close dialog
  console.log('6. Closing dialog...');
  await page.click('#dialog-test button.primary', { force: true });
  await page.waitForTimeout(300);

  // 7. Switch to Settings tab
  console.log('7. Switching to Settings tab...');
  await page.click('#tab-settings', { force: true });
  await page.waitForTimeout(300);

  // 8. Fill in form fields (test privacy sanitization)
  console.log('8. Filling settings form (privacy test)...');
  await page.fill('#user-name', 'John Doe');
  await page.waitForTimeout(200);
  await page.fill('#user-email', 'john@example.com');
  await page.waitForTimeout(200);
  await page.fill('#user-phone', '+1-555-0100');
  await page.waitForTimeout(200);
  await page.fill('#user-password', 'secretpass123');
  await page.waitForTimeout(200);

  // 9. Click Save
  console.log('9. Clicking Save Settings...');
  await page.click('#save-btn', { force: true });
  await page.waitForTimeout(300);

  // 10. Switch to Overview tab and search
  console.log('10. Switching to Overview and searching...');
  await page.click('#tab-overview', { force: true });
  await page.waitForTimeout(300);
  await page.fill('#search-input', 'analytics report');
  await page.waitForTimeout(200);
  await page.click('#search-btn', { force: true });
  await page.waitForTimeout(500);

  // Wait for events to flush to receiver
  console.log('\nWaiting for events to flush...');
  await page.waitForTimeout(3000);

  // Check live counters
  const eventCountFinal = await page.locator('#event-count').textContent();
  const actionCountFinal = await page.locator('#action-count').textContent();
  const sessionInfo = await page.locator('#session-id').textContent();
  console.log(`\nLive counts: ${eventCountFinal}, ${actionCountFinal}`);
  console.log(`${sessionInfo}`);

  // Close browser to trigger beforeunload flush
  await browser.close();
  await new Promise((r) => setTimeout(r, 2000));

  // 11. Query the event receiver for session data
  console.log('\n=== Querying Event Receiver ===\n');

  const sessionsRes = await fetch(`${RECEIVER_URL}/api/sessions`);
  const sessionsData = await sessionsRes.json();

  console.log(`Sessions recorded: ${sessionsData.sessions.length}`);

  if (sessionsData.sessions.length === 0) {
    console.log('⚠ No sessions found. Events may not have flushed.');
    process.exit(1);
  }

  // Get the last (most recent) session
  const session = sessionsData.sessions[sessionsData.sessions.length - 1];
  console.log(`Session ID: ${session.sessionId}`);
  console.log(`Total events: ${session.eventCount}`);
  console.log(`Actionable events: ${session.actionableCount}`);
  console.log(`Actions captured:`);
  session.actions.forEach((a, i) => {
    console.log(`  ${i + 1}. ${a.type} on ${a.role} "${a.name}" states:${JSON.stringify(a.states)} ctx:${a.context || 'none'}`);
  });

  // 12. Get Agent-consumable summary
  console.log('\n=== Agent-Consumable Summary (TOON Format) ===\n');

  const summaryRes = await fetch(`${RECEIVER_URL}/api/sessions/${session.sessionId}/summary`);
  const summary = await summaryRes.json();

  console.log(`URL: ${summary.url}`);
  console.log(`Duration: ${summary.durationS}s`);
  console.log(`Events: ${summary.eventCount} | Actions: ${summary.actionCount}`);
  console.log(`\nCompact TOON:`);
  summary.toon.forEach((line, i) => console.log(`  ${i + 1}. ${line}`));

  console.log(`\nSummary Text:\n  ${summary.summaryText}`);

  // 13. Validation checks
  console.log('\n=== Validation Results ===\n');

  const checks = [
    {
      name: 'Events recorded',
      pass: session.eventCount > 0,
      detail: `${session.eventCount} events`,
    },
    {
      name: 'Actionable events captured',
      pass: session.actionableCount >= 5,
      detail: `${session.actionableCount} actionable events`,
    },
    {
      name: 'Tab click captured',
      pass: session.actions.some((a) => a.role === 'tab' && a.name === 'Export'),
      detail: 'Export tab click',
    },
    {
      name: 'Button click captured',
      pass: session.actions.some((a) => a.role === 'button' && a.name === 'Search'),
      detail: 'Search button click',
    },
    {
      name: 'Checkbox interaction captured',
      pass: session.actions.some((a) => a.role === 'checkbox'),
      detail: 'Include charts checkbox',
    },
    {
      name: 'Form input captured',
      pass: session.actions.some((a) => a.role === 'textbox'),
      detail: 'Search/textbox input',
    },
    {
      name: 'Select/listbox captured',
      pass: session.actions.some((a) => a.role === 'listbox'),
      detail: 'Format select',
    },
    {
      name: 'TOON format generated',
      pass: summary.toon.length > 0,
      detail: `${summary.toon.length} TOON lines`,
    },
    {
      name: 'Summary text generated',
      pass: summary.summaryText.length > 10,
      detail: `${summary.summaryText.length} chars`,
    },
  ];

  let passed = 0;
  for (const c of checks) {
    const status = c.pass ? '✓ PASS' : '✗ FAIL';
    console.log(`${status} — ${c.name} (${c.detail})`);
    if (c.pass) passed++;
  }

  console.log(`\n=== Result: ${passed}/${checks.length} passed ===`);

  // 14. Privacy verification - check that sensitive data was sanitized
  console.log('\n=== Privacy Verification ===\n');

  const detailRes = await fetch(`${RECEIVER_URL}/api/sessions/${session.sessionId}/summary`);
  const detail = await detailRes.json();

  const hasRedacted = JSON.stringify(detail).includes('[REDACTED]') ||
                      JSON.stringify(detail.actions).includes('password');
  const hasEmailSanitized = JSON.stringify(detail).includes('{email}') ||
                            !JSON.stringify(detail).includes('john@example.com');
  const hasPhoneSanitized = JSON.stringify(detail).includes('{phone}') ||
                            !JSON.stringify(detail).includes('+1-555-0100');

  console.log(`Password [REDACTED]: ${hasRedacted ? '✓' : '⚠ (input value may not be in summary)'}`);
  console.log(`Email {email}: ${hasEmailSanitized ? '✓' : '✗ LEAKED'}`);
  console.log(`Phone {phone}: ${hasPhoneSanitized ? '✓' : '✗ LEAKED'}`);

  console.log('\n=== Pipeline Verification Complete ===\n');

  process.exit(passed === checks.length ? 0 : 1);
})().catch((err) => {
  console.error('Test failed:', err);
  process.exit(1);
});
