---
name: mss-sop
description: |
  Execute MSS platform SOP (Standard Operating Procedure) definitions. Reads a SOP YAML
  file and performs the defined API calls with parameter substitution and response handling.
  Use when the user wants to: (1) Run a pre-defined SOP, (2) Execute security operations
  automatically, (3) Process alerts via SOP. Triggers: "execute SOP", "run SOP",
  "SOP execute", "process alert", "run procedure", "MSS SOP".
---

# MSS SOP Executor

Execute pre-defined SOP workflows against the MSS platform API.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sop_name` | string | _(required)_ | Name of the SOP in config/mss_sops/ (without extension) |
| `params` | object | `{}` | Input parameters for SOP execution as JSON object |
| `report_path` | string | _(auto)_ | Report save path, injected by runner |

## Workflow

1. **Validate SOP**: Use Bash to run `python -m src.mss validate --sop <sop_name>`. Check the output confirms the SOP is valid and lists required parameters.

2. **Check Parameters**: Verify all required parameters from the SOP's `input_parameters` are provided in the `params` object. If any are missing, report which ones are needed and stop.

3. **Execute SOP**: Use Bash to run the execution command:
   ```
   python -m src.mss execute --sop <sop_name> --params '<params_json>'
   ```
   The `--params` value must be a valid JSON string. Ensure proper escaping of quotes.

4. **Collect Results**: The execution command outputs a JSON result with:
   - `status`: "success", "failed", or "partial"
   - `steps[]`: Each step's status, HTTP status code, extracted variables, and any errors
   - `output`: The SOP's output summary and key fields
   - `error`: Top-level error message if the SOP failed

5. **Report**: Generate an execution report containing:
   - SOP name and execution status
   - Step-by-step results (which steps succeeded, failed, or were skipped)
   - Extracted variables from each step
   - Final output summary
   - Any errors encountered
   Save the report to `report_path`.

## Execution Guide

See `assets/execution-guide.md` for details on the execution engine internals.

## Error Handling

- If authentication fails, report the error and suggest checking `config/mss_auth.yaml`
- If a step's HTTP status doesn't match `expect.status`, the SOP stops and reports which step failed
- If the SOP is not found, list available SOPs using `python -m src.mss list-sops`
- Timeout is 60 seconds per HTTP request; if the MSS platform is slow, note this in the report

## Notes

- `params` must be a valid JSON object. When passing via slash command, ensure proper quoting
- The execution engine handles `{{variable}}` substitution automatically
- Condition steps (`condition` field) are evaluated before execution; skipped steps are reported
- Execution records are saved to `data/mss_executions/YYYY-MM-DD/` automatically
- Use Chinese for report body; keep technical terms in English
