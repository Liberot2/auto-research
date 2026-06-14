#!/usr/bin/env node
/**
 * replay-a11y.js — 从 Umami 读取 A11y 事件并回放操作
 *
 * 用法:
 *   node replay-a11y.js                  # 回放最新 session
 *   node replay-a11y.js --dry-run        # 只打印回放计划
 *   node replay-a11y.js --session <id>   # 回放指定 session
 *   node replay-a11y.js --headed         # 显示浏览器窗口
 *   node replay-a11y.js --url <url>      # 目标页面
 */
const { chromium } = require('playwright');
const { execSync } = require('child_process');

// ========================================
// CLI 参数
// ========================================
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const HEADED = args.includes('--headed');
const SESSION_FLAG = args.indexOf('--session');
const SESSION_ID = SESSION_FLAG >= 0 ? args[SESSION_FLAG + 1] : null;
const URL_FLAG = args.indexOf('--url');
const TARGET_URL = URL_FLAG >= 0 ? args[URL_FLAG + 1] : 'http://localhost:8080';

// ========================================
// 从 Umami PostgreSQL 读取事件
// ========================================
function fetchEvents(sessionId) {
  const pyPath = 'e:/workspace/auto-research/docker/test/fetch_events.py'.replace(/\//g, '/');
  const wslPath = '/mnt/' + pyPath.replace(':', '').replace(/\//g, '/');
  const cmd = `wsl -d Ubuntu bash -c "python3 /mnt/e/workspace/auto-research/docker/test/fetch_events.py ${sessionId || ''}"`;
  const output = execSync(cmd, { encoding: 'utf-8', maxBuffer: 1024 * 1024 });
  const rawEvents = JSON.parse(output.trim());

  return rawEvents.map(ev => ({
    eventId: '',
    createdAt: '',
    eventType: ev.eventtype || ev.eventType || '',
    role: ev.role || '',
    name: ev.name || '',
    toon: ev.toon || '',
    sessionId: ev.sessionid || ev.sessionId || '',
    timestamp: parseInt(ev.timestamp) || 0,
    context: { role: ev.contextrole || ev.contextRole || '', label: ev.contextlabel || ev.contextLabel || '' },
    selectedText: ev.selectedtext || ev.selectedText || '',
    inputValue: ev.inputvalue || ev.inputValue || '',
    pageSessionId: ev.pagesessionid || ev.pageSessionId || '',
  }));
}

// ========================================
// 事件去重与过滤
// ========================================
function deduplicateEvents(events) {
  const filtered = [];
  let lastSig = null;
  let lastTs = 0;

  for (const ev of events) {
    // 跳过 change 事件（由 fill/selectOption 自动触发），但保留 listbox change（包含选中值）
    if (ev.eventType === 'change' && ev.role !== 'listbox') continue;

    // checkbox: click 和 input 是同一操作，只保留 click，跳过后续 input
    if (ev.eventType === 'input' && ev.role === 'checkbox') {
      if (lastSig === 'click:checkbox:' + ev.name && ev.timestamp - lastTs < 500) continue;
    }

    // 去重: 300ms 内同 role+name+eventType
    const sig = `${ev.eventType}:${ev.role}:${ev.name}`;
    if (sig === lastSig && ev.timestamp - lastTs < 300) continue;
    lastSig = sig;
    lastTs = ev.timestamp;

    filtered.push(ev);
  }

  return filtered;
}

// ========================================
// 输入值推断
// ========================================
function inferInputValue(name) {
  const n = (name || '').toLowerCase();
  if (n.includes('search')) return 'replay-search-query';
  if (n.includes('name')) return 'Replay User';
  if (n.includes('email')) return 'replay@test.com';
  if (n.includes('phone') || n.includes('tel')) return '+1-555-0199';
  if (n.includes('password')) return 'replay-pass-123';
  if (n.includes('address')) return '123 Replay St';
  return 'replay-value';
}

function inferSelectOption(name) {
  const n = (name || '').toLowerCase();
  if (n.includes('format') || n.includes('export')) return 'csv';
  return 'csv'; // default to CSV for demo
}

// ========================================
// Playwright 回放
// ========================================
async function replay(events, url, headed) {
  const browser = await chromium.launch({ headless: !headed });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
  });
  const page = await context.newPage();

  console.log(`\nNavigating to ${url}...`);
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  const results = [];

  for (let i = 0; i < events.length; i++) {
    const ev = events[i];
    const step = i + 1;
    const label = `[${step}/${events.length}] ${ev.toon}`;

    try {
      if (ev.eventType === 'click') {
        let locator;
        if (ev.name) {
          locator = page.getByRole(ev.role, { name: ev.name });
        } else if (ev.role === 'checkbox') {
          // Fallback: find checkbox by nearby text in same context panel
          locator = page.locator('input[type="checkbox"]').first();
        } else {
          locator = page.getByRole(ev.role).first();
        }
        await locator.click({ timeout: 5000, force: true });
        results.push({ step, label, status: 'PASS', detail: '' });
        console.log(`  PASS: ${label}`);

      } else if (ev.eventType === 'input' && ev.role === 'checkbox') {
        // Checkbox toggle: click instead of fill
        let locator;
        if (ev.name) {
          locator = page.getByRole('checkbox', { name: ev.name });
        } else {
          locator = page.locator('input[type="checkbox"]').first();
        }
        await locator.click({ timeout: 5000, force: true });
        results.push({ step, label, status: 'PASS', detail: 'toggled' });
        console.log(`  PASS: ${label} (toggle)`);

      } else if (ev.eventType === 'input' && ev.role === 'listbox') {
        // Select dropdown: use selectOption with captured value or inference
        const locator = page.getByRole('listbox', { name: ev.name });
        const optionText = ev.selectedText || inferSelectOption(ev.name);
        // Try matching by visible text first, then by value
        try {
          await locator.selectOption({ label: optionText });
        } catch (e) {
          await locator.selectOption(optionText.toLowerCase());
        }
        results.push({ step, label, status: 'PASS', detail: `selected="${optionText}"` });
        console.log(`  PASS: ${label} → "${optionText}"`);

      } else if (ev.eventType === 'input') {
        const value = ev.inputValue || inferInputValue(ev.name);
        const locator = page.getByRole(ev.role, { name: ev.name });
        await locator.click({ timeout: 5000, force: true });
        await page.waitForTimeout(300);
        await locator.fill(value, { timeout: 5000 });
        results.push({ step, label, status: 'PASS', detail: `filled="${value}"` });
        console.log(`  PASS: ${label} → "${value}"`);

      } else {
        results.push({ step, label, status: 'SKIP', detail: `unhandled eventType: ${ev.eventType}` });
        console.log(`  SKIP: ${label}`);
      }

      await page.waitForTimeout(1500);

    } catch (err) {
      results.push({ step, label, status: 'FAIL', detail: err.message.split('\n')[0] });
      console.log(`  FAIL: ${label} — ${err.message.split('\n')[0]}`);
    }
  }

  // Take screenshot of final state
  const screenshotPath = 'e:/workspace/auto-research/docker/test/replay-result.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`\nScreenshot: ${screenshotPath}`);

  await browser.close();
  return results;
}

// ========================================
// Main
// ========================================
(async () => {
  console.log('=== A11y Operation Replay ===');
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}, Target: ${TARGET_URL}\n`);

  // 1. Fetch events
  console.log('Fetching a11y-action events from Umami...');
  const sessionEvents = fetchEvents(SESSION_ID);

  if (sessionEvents.length === 0) {
    console.log('No a11y-action events found.');
    process.exit(1);
  }

  const targetSession = sessionEvents[0]?.sessionId || 'latest';
  console.log(`Target session: ${targetSession.slice(0, 8)}... (${sessionEvents.length} raw events)`);

  // 2. Deduplicate
  const cleanEvents = deduplicateEvents(sessionEvents);
  console.log(`After dedup/filter: ${cleanEvents.length} actions\n`);

  if (cleanEvents.length === 0) {
    console.log('No replayable actions after filtering.');
    process.exit(0);
  }

  // 3. Dry run or live replay
  if (DRY_RUN) {
    console.log('=== Replay Plan (dry run) ===\n');
    cleanEvents.forEach((ev, i) => {
      const value = ev.eventType === 'input' ? ` → fill("${inferInputValue(ev.name)}")` : '';
      console.log(`  ${i + 1}. ${ev.toon}${value}`);
    });
    console.log(`\nTotal: ${cleanEvents.length} actions ready for replay.`);
  } else {
    console.log('=== Live Replay ===\n');
    const results = await replay(cleanEvents, TARGET_URL, HEADED);

    const passed = results.filter(r => r.status === 'PASS').length;
    const failed = results.filter(r => r.status === 'FAIL').length;
    const skipped = results.filter(r => r.status === 'SKIP').length;

    console.log(`\n=== Result: ${passed} PASS, ${failed} FAIL, ${skipped} SKIP ===`);
    console.log(`Success rate: ${Math.round(passed / (passed + failed) * 100)}%\n`);

    // Save report
    const fs = require('fs');
    fs.writeFileSync(
      'e:/workspace/auto-research/docker/test/replay-report.json',
      JSON.stringify({ session: targetSession, url: TARGET_URL, results, passed, failed, skipped }, null, 2)
    );
  }

  process.exit(0);
})();
