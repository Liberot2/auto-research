import express from "express";
import { writeFileSync, readFileSync, existsSync, mkdirSync, readdirSync } from "fs";
import { join } from "path";

const app = express();
const PORT = process.env.PORT || 3000;
const STORAGE = process.env.STORAGE_DIR || "/data/events";

// CORS — allow demo app to send events
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.header("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.sendStatus(204);
  next();
});

app.use(express.json({ limit: "50mb" }));

// Ensure storage dir
if (!existsSync(STORAGE)) mkdirSync(STORAGE, { recursive: true });

// POST /api/events — receive a batch of RRWeb events
app.post("/api/events", (req, res) => {
  const { sessionId, events } = req.body;
  if (!sessionId || !events || !Array.isArray(events)) {
    return res.status(400).json({ error: "sessionId and events[] required" });
  }

  const dir = join(STORAGE, sessionId);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  // Append events as JSONL
  const file = join(dir, "events.jsonl");
  const lines = events.map((e) => JSON.stringify(e)).join("\n") + "\n";
  const existing = existsSync(file) ? readFileSync(file, "utf-8") : "";
  writeFileSync(file, existing + lines, "utf-8");

  // Count actionable events (those with _a11y)
  const actionable = events.filter((e) => e._a11y?.actionable).length;

  res.json({
    status: "ok",
    sessionId,
    received: events.length,
    actionable,
  });
});

// GET /api/sessions — list all sessions
app.get("/api/sessions", (req, res) => {
  const dir = STORAGE;
  if (!existsSync(dir)) return res.json({ sessions: [] });

  const sessions = readdirSync(dir).map((sid) => {
    const file = join(dir, sid, "events.jsonl");
    if (!existsSync(file)) return null;
    const content = readFileSync(file, "utf-8");
    const lines = content.trim().split("\n").filter(Boolean);
    const events = lines.map((l) => {
      try { return JSON.parse(l); } catch { return null; }
    }).filter(Boolean);

    const actionable = events.filter((e) => e._a11y?.actionable);
    const firstTs = events[0]?.timestamp || 0;
    const lastTs = events[events.length - 1]?.timestamp || 0;

    return {
      sessionId: sid,
      eventCount: events.length,
      actionableCount: actionable.length,
      durationMs: lastTs - firstTs,
      actions: actionable.map((e) => ({
        type: e._a11y?.role ? inferActionType(e) : "dom",
        role: e._a11y?.role || "unknown",
        name: e._a11y?.name || "",
        states: e._a11y?.states || {},
        context: e._a11y?.context?.label || "",
        timestamp: e.timestamp,
      })),
    };
  }).filter(Boolean);

  res.json({ sessions });
});

// GET /api/sessions/:id/summary — Agent-consumable session summary
app.get("/api/sessions/:id/summary", (req, res) => {
  const file = join(STORAGE, req.params.id, "events.jsonl");
  if (!existsSync(file)) {
    return res.status(404).json({ error: "Session not found" });
  }

  const content = readFileSync(file, "utf-8");
  const events = content.trim().split("\n").filter(Boolean).map((l) => {
    try { return JSON.parse(l); } catch { return null; }
  }).filter(Boolean);

  const actionable = events.filter((e) => e._a11y?.actionable);
  const firstTs = events[0]?.timestamp || 0;
  const lastTs = events[events.length - 1]?.timestamp || 0;

  // Build Compact TOON format
  const toonLines = actionable.map((e, i) => {
    const a = e._a11y;
    const states = Object.keys(a.states).length
      ? ` s:{${Object.entries(a.states).map(([k, v]) => `${k}:${v}`).join(",")}}`
      : "";
    const ctx = a.context?.label ? ` ctx:${a.context.role}("${a.context.label}")` : "";
    const action = inferActionType(e);
    return `${action} r:${a.role} n:"${a.name}"${states}${ctx}`;
  });

  // Build summary text
  const summaryText = generateSummaryText(actionable);

  res.json({
    sessionId: req.params.id,
    url: events.find((e) => e.type === 4)?.data?.href || "",
    durationS: Math.round((lastTs - firstTs) / 1000),
    eventCount: events.length,
    actionCount: actionable.length,
    // Compact TOON format
    toon: toonLines,
    // Summary text for LLM
    summaryText,
    // Raw actions for detailed analysis
    actions: actionable.map((e, i) => ({
      i: i + 1,
      type: inferActionType(e),
      role: e._a11y.role,
      name: e._a11y.name,
      states: e._a11y.states,
      context: e._a11y.context?.label || null,
      timestamp: e.timestamp,
    })),
  });
});

function inferActionType(event) {
  if (event._a11y?.actionable) {
    if (event.data?.source === 2) {
      const clickTypes = ["click", "dblclick", "mouseup", "mousedown", "touchend"];
      return clickTypes[event.data.type] || "click";
    }
    if (event.data?.source === 5) return "input";
    if (event.data?.source === 1) return "move";
  }
  return "dom-change";
}

function generateSummaryText(actionableEvents) {
  if (!actionableEvents.length) return "No actionable events recorded.";

  const actions = actionableEvents.map((e) => {
    const a = e._a11y;
    const parts = [`${a.role} "${a.name}"`];
    if (a.states && Object.keys(a.states).length) {
      parts.push(`[${Object.entries(a.states).map(([k, v]) => `${k}=${v}`).join(",")}]`);
    }
    return parts.join(" ");
  });

  return `User performed ${actions.length} actions: ${actions.join(" → ")}`;
}

app.listen(PORT, () => {
  console.log(`RRWeb event receiver listening on :${PORT}`);
});
