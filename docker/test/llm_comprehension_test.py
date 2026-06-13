"""
LLM Comprehension Test — verify Agent can consume TOON event stream.
Feeds the Compact TOON session data to Claude and tests 5 reasoning tasks.
"""
import json
import os
import sys

# Load session data
with open("e:/workspace/auto-research/docker/test/session_data.json", encoding="utf-8") as f:
    session = json.load(f)

# Build Compact TOON prompt
toon_lines = "\n".join(f"  {i+1}. {line}" for i, line in enumerate(session.get("toon", [])))

llm_prompt = f"""You are a UX analysis Agent. Below is a user session recorded as Compact TOON (Accessibility-enhanced) event stream.

## Session Data
URL: {session.get('url','')}
Duration: {session.get('durationS',0)}s
Total Actions: {session.get('actionCount',0)}

### Action Sequence (Compact TOON format)
{toon_lines}

### Summary
{session.get('summaryText','')}

---

## Analysis Tasks

Based ONLY on the TOON event stream above, answer these questions:

1. **User Intent**: What was the user's primary goal in this session? (1 sentence)

2. **Page Flow**: List the pages/tabs the user navigated through in order.

3. **Form Analysis**: Which form fields did the user fill in? What privacy concerns exist?

4. **Interaction Patterns**: Did the user encounter any friction or hesitation? (e.g., multiple clicks on same element, back-and-forth navigation)

5. **Actionable Recommendations**: Based on this session, suggest 2 UX improvements.

Be concise. Use evidence from the TOON data to support each answer.
"""

print("=== LLM Prompt (Compact TOON) ===")
print(f"Prompt size: {len(llm_prompt)} chars (~{len(llm_prompt)//4} tokens)")
print()
print(llm_prompt[:1000])
print("...")
print()

# Now test via Claude Agent SDK
print("=== Sending to Claude Agent SDK for comprehension ===")
print()

try:
    import asyncio
    from claude_agent_sdk import query, ClaudeAgentOptions

    async def run_test():
        options = ClaudeAgentOptions(
            max_turns=3,
            permission_mode="bypassPermissions",
            setting_sources=["project", "local"],
        )

        response_text = []
        async for message in query(prompt=llm_prompt, options=options):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        response_text.append(block.text)
            elif isinstance(message, str):
                response_text.append(message)

        return "\n".join(response_text)

    result = asyncio.run(run_test())
    print("=== Agent Response ===")
    print(result)

    # Validation checks
    print("\n=== Comprehension Validation ===\n")

    checks = []

    # 1. User intent should mention export/settings/search
    checks.append((
        "User intent identified",
        any(w in result.lower() for w in ["export", "settings", "search", "configure", "report"]),
    ))

    # 2. Page flow should list tabs
    checks.append((
        "Page flow traced",
        any(w in result.lower() for w in ["overview", "export", "settings", "tab", "dashboard"]),
    ))

    # 3. Form analysis should identify fields
    checks.append((
        "Form fields identified",
        any(w in result.lower() for w in ["name", "email", "phone", "password", "textbox", "form"]),
    ))

    # 4. Privacy concern mentioned
    checks.append((
        "Privacy concerns noted",
        any(w in result.lower() for w in ["password", "email", "phone", "privacy", "pii", "sensitive", "personal"]),
    ))

    # 5. UX recommendations provided
    checks.append((
        "UX recommendations given",
        any(w in result.lower() for w in ["improve", "suggest", "recommend", "should", "could", "consider"]),
    ))

    # 6. TOON data referenced (evidence-based)
    checks.append((
        "Evidence from TOON cited",
        any(w in result.lower() for w in ["toon", "action", "sequence", "event", "click", "input", "tab"]),
    ))

    passed = 0
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {name}")
        if ok:
            passed += 1

    print(f"\n=== Result: {passed}/{len(checks)} comprehension checks passed ===")

    # Save result
    with open("e:/workspace/auto-research/docker/test/llm_response.txt", "w", encoding="utf-8") as f:
        f.write(f"=== PROMPT ===\n\n{llm_prompt}\n\n=== RESPONSE ===\n\n{result}\n\n=== VALIDATION ===\n")
        for name, ok in checks:
            f.write(f"  {'PASS' if ok else 'FAIL'}: {name}\n")
        f.write(f"\nResult: {passed}/{len(checks)}\n")

    sys.exit(0 if passed >= 5 else 1)

except ImportError:
    print("claude_agent_sdk not available, using manual evaluation")
    print("Please review the prompt above and evaluate manually.")
    sys.exit(2)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
