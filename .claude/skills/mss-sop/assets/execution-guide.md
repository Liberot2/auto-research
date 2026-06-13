# SOP Execution Engine Guide

## Architecture

The execution engine lives in `src/mss/` and provides the HTTP infrastructure for SOP execution.

### Modules

| Module | Responsibility |
|--------|---------------|
| `src/mss/executor.py` | Main execution loop: load SOP, validate, run steps, save results |
| `src/mss/auth.py` | Authentication: load credentials, obtain tokens, build auth headers |
| `src/mss/substitution.py` | Template resolution: `{{var}}` replacement, condition evaluation, JSONPath extraction |

### Execution Flow

```
SopExecutor.run(sop_name, params)
  1. load_sop() -> Parse YAML
  2. validate_inputs() -> Check required params
  3. auth.get_token() -> Obtain session token
  4. For each step:
     a. Check condition -> skip if false
     b. resolve_templates() -> Replace {{var}} in path/headers/body
     c. httpx.request() -> Make HTTP call
     d. Validate response status
     e. extract_variables() -> Extract values via JSONPath
     f. Merge into context for next step
  5. Build output from final context
  6. Save execution record to data/mss_executions/
```

### JSONPath Support

The engine supports a simplified JSONPath for extracting values:
- `$.data.token` -> `response["data"]["token"]`
- `$.data.items[0].id` -> `response["data"]["items"][0]["id"]`

### Condition Evaluation

Conditions are simple string comparisons:
- `{{threat_level}} == 'high'` -> True if threat_level is "high"
- `{{count}} > 10` -> True if count is a number greater than 10
- `{{status}} != 'closed'` -> True if status is not "closed"

### CLI Usage

```bash
# List available SOPs
python -m src.mss list-sops

# Validate a SOP
python -m src.mss validate --sop handle_alert

# Execute a SOP
python -m src.mss execute --sop handle_alert --params '{"alert_id": "ALT-12345"}'
```
