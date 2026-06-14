"""Fetch A11y events from Umami PostgreSQL as JSON."""
import subprocess, json, sys

session_id = sys.argv[1] if len(sys.argv) > 1 else ""

# If no session specified, find the latest one first
if not session_id:
    latest_sql = (
        "SELECT ed.string_value FROM event_data ed "
        "JOIN website_event we ON ed.website_event_id = we.event_id "
        "WHERE ed.data_key = 'pageSessionId' AND we.event_name = 'a11y-action' "
        "ORDER BY we.created_at DESC LIMIT 1;"
    )
    result = subprocess.run(
        ["docker", "exec", "umami-db", "psql", "-U", "umami", "-t", "-A", "-c", latest_sql],
        capture_output=True, text=True
    )
    session_id = result.stdout.strip()
    if not session_id:
        print("[]")
        sys.exit(0)

session_filter = (
    "AND we.event_id IN (SELECT website_event_id FROM event_data "
    "WHERE data_key = 'pageSessionId' AND string_value = '" + session_id + "')"
)

sql = (
    "SELECT row_to_json(t) FROM ("
    "  SELECT"
    "    MAX(CASE WHEN ed.data_key = 'eventType' THEN ed.string_value END) as eventType,"
    "    MAX(CASE WHEN ed.data_key = 'role' THEN ed.string_value END) as role,"
    "    MAX(CASE WHEN ed.data_key = 'name' THEN ed.string_value END) as name,"
    "    MAX(CASE WHEN ed.data_key = 'toon' THEN ed.string_value END) as toon,"
    "    MAX(CASE WHEN ed.data_key = 'sessionId' THEN ed.string_value END) as sessionId,"
    "    MAX(CASE WHEN ed.data_key = 'timestamp' THEN ed.number_value END) as timestamp,"
    "    MAX(CASE WHEN ed.data_key = 'context.role' THEN ed.string_value END) as contextRole,"
    "    MAX(CASE WHEN ed.data_key = 'context.label' THEN ed.string_value END) as contextLabel,"
    "    MAX(CASE WHEN ed.data_key = 'selectedText' THEN ed.string_value END) as selectedText,"
    "    MAX(CASE WHEN ed.data_key = 'inputValue' THEN ed.string_value END) as inputValue,"
    "    MAX(CASE WHEN ed.data_key = 'pageSessionId' THEN ed.string_value END) as pageSessionId"
    "  FROM website_event we"
    "  JOIN event_data ed ON we.event_id = ed.website_event_id"
    "  WHERE we.event_name = 'a11y-action'"
    "  " + session_filter +
    "  GROUP BY we.event_id, we.created_at"
    "  ORDER BY we.created_at ASC"
    "  LIMIT 100"
    ") t;"
)

result = subprocess.run(
    ["docker", "exec", "umami-db", "psql", "-U", "umami", "-t", "-A", "-c", sql],
    capture_output=True, text=True
)

events = []
for line in result.stdout.strip().split("\n"):
    line = line.strip()
    if line:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

print(json.dumps(events))
