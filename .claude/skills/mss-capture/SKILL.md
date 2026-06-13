---
name: mss-capture
description: |
  Review captured MSS platform HTTP actions and generate SOP (Standard Operating Procedure)
  YAML definitions. Use when the user wants to: (1) Convert captured browser actions into
  automated SOPs, (2) Review and clean up captured HTTP sessions, (3) Generate SOP templates
  from action recordings. Triggers: "capture review", "generate SOP", "action to SOP",
  "capture to sop", "SOP generate", "MSS capture", "action capture".
---

# MSS Action Capture to SOP Generator

Review captured HTTP sessions from the MSS platform and generate structured SOP definitions.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `capture_file` | string | _(required)_ | Path to capture JSON file in data/mss_captures/ |
| `sop_name` | string | _(auto)_ | Name for the generated SOP. Auto-derived from capture if not provided |
| `report_path` | string | _(auto)_ | Report save path, injected by runner |

## Workflow

1. **Load Capture**: Read the JSON file at `capture_file` using the Read tool. Parse the `actions` array.

2. **Analyze Patterns**: Examine the request sequence to identify:
   - API endpoint patterns (group by base path)
   - Request method per endpoint (GET, POST, PUT, DELETE)
   - Common query parameters
   - Request body structure
   - Response status codes
   - Temporal ordering (which calls happen in sequence)

3. **Identify Dynamic Parameters**: For each action, determine which values are:
   - **Dynamic** (IDs, timestamps, IPs, tokens) -> These become `{{variable}}` templates
   - **Static** (fixed enum values, content types) -> Keep as-is
   - Heuristic: numeric-only strings, UUIDs, IP-like patterns, timestamps are likely dynamic
   - If a value from a response body appears in a later request's URL or body, it's an extracted variable

4. **Generate SOP**: Write a YAML SOP definition following the template at `assets/sop-template.yaml`. Include:
   - `name` and `description` based on the operation pattern
   - `base_url` from the capture metadata
   - `auth.profile` placeholder (user will configure)
   - `input_parameters` for all dynamic values identified
   - `steps` array with method, path, body templates, expected status, and extract rules
   - `output` section with summary template and key fields

5. **Save SOP**: Write the SOP YAML to `config/mss_sops/<sop_name>.yaml` using the Write tool.

6. **Report**: Generate a summary report describing:
   - Number of captured actions analyzed
   - API endpoints discovered
   - Dynamic parameters identified
   - SOP steps generated
   - Saved SOP file path
   Save the report to `report_path`.

## Notes

- If `sop_name` is not provided, derive it from the capture session's operation pattern (e.g., "handle_alert" if the actions involve alert-related APIs)
- Remove duplicate or redundant requests (e.g., polling/heartbeat calls)
- Skip authentication/login requests in the capture (they're handled by the auth config)
- Group related requests that operate on the same resource ID
- Response bodies in captures may be truncated; note this in the SOP description if relevant
- Use Chinese for SOP `name` and `description` fields if the MSS platform is Chinese-language
