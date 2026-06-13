import json

with open("e:/workspace/auto-research/docker/test/session_data.json", encoding="utf-8") as f:
    d = json.load(f)

prompt = f"""## User Session: {d.get('url','')}
Duration: {d.get('durationS',0)}s | Actions: {d.get('actionCount',0)}

### Action Sequence (Compact TOON)
"""
for line in d.get("toon", []):
    prompt += line + "\n"

prompt += f"""
### Navigation
Dashboard -> Export tab -> Settings tab -> Overview tab

### Summary
{d.get('summaryText','')}
"""

with open("e:/workspace/auto-research/docker/test/llm_prompt.txt", "w") as f:
    f.write(prompt)

print(f"Prompt length: {len(prompt)} chars")
print("---")
print(prompt[:800])
