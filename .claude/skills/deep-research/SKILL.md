---
name: deep-research
description: |
  Multi-session agentic deep research system. Autonomously conducts phased research
  (Discovery, Analysis, Solution Draft, Validation, Finalization) across multiple
  scheduled invocations. Each run advances the research by reading state, performing
  the next logical action, and writing state back. Produces complete solution documents
  with executable verification checklists.
  Triggers: "deep research", "research project", "comprehensive analysis",
  "solution document", "deep-research", "方案研究", "深度研究".
---

# Deep Research

Multi-session agentic research focused on **technology solution evaluation and selection**.
Progresses through phases to produce a complete, actionable solution document with verification checklist.

## Research Focus: Technology Solution Selection

This skill is optimized for technology solution evaluation. The core output is a **decision-making document** that:
- Compares candidate solutions objectively
- Provides a clear recommendation with evidence
- Includes an executable implementation plan
- Is practical enough for you to act on immediately

When researching, prioritize:
- **Concrete comparisons**: Side-by-side feature/metric tables, not vague descriptions
- **Real-world evidence**: Benchmarks, case studies, production usage data, not just marketing claims
- **Trade-off analysis**: Every choice has costs; make them explicit
- **Decision criteria**: Define what "good" looks like early, then evaluate against it

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project` | string | _(required)_ | Project slug, maps to `data/research/{project}/` |
| `topic` | string | `""` | Research topic (required on first run to initialize) |
| `max_depth` | integer | `3` | Research depth per phase (1-5) |
| `focus` | string | `""` | Specific sub-topic to focus on this session |
| `research_dir` | string | `data/research` | Base directory (injected by runner) |
| `report_path` | string | _(auto)_ | Session report save path (injected by runner) |

## Research Phases

The research progresses through these phases automatically:

1. **discovery** - Broad search for information, collect sources, identify knowledge gaps
2. **analysis** - Synthesize sources, identify patterns, compare approaches, evaluate evidence
3. **solution_draft** - Draft solution document sections based on analysis
4. **validation** - Validate solution against checklist, test key claims, identify risks
5. **finalization** - Polish solution document, finalize checklist, produce deliverable
6. **complete** - Research finished, solution document is finalized

## Research TODO (Cross-Session Relay)

Every research project maintains a `research-todo.md` as the **relay baton** between sessions. This file is the single source of truth for what needs to be done, what's been done, and what's next.

### TODO Structure

```markdown
# Research TODO: {project}

## Overview
{1-2 sentence description of the research goal}

## Phase: {current_phase}

### ✅ Completed
- [x] {item} — {session_id or date} — {brief finding/conclusion}

### 🔄 In Progress
- [ ] {item} — started {date} — {notes on current state}

### 📋 Pending (Ordered by Priority)
- [ ] {item} — {why it's needed, what question it answers}
- [ ] {item}

### ❓ Open Questions
- {question that needs resolution before proceeding}

### 📎 Key Decisions Made
- {decision}: {rationale} — {date}
```

### TODO Lifecycle

1. **Project init**: Generate TODO items from the research topic, covering all phases
2. **Session start**: Read TODO → understand progress → plan this session's focus
3. **During session**: Check off completed items, add new items discovered
4. **Session end**: Update TODO with findings, reorder priorities, set next focus
5. **Phase transition**: Re-evaluate all remaining items, promote/demote based on new understanding

## Phase Transition Criteria

Advance to next phase when current phase objectives are met:

- **discovery -> analysis**: Confidence >= 70%, sufficient sources collected, knowledge gaps mapped
- **analysis -> solution_draft**: Pattern analysis complete, approach direction identified, evidence evaluated
- **solution_draft -> validation**: All major solution sections drafted with concrete content
- **validation -> finalization**: All checklist items addressed or deferred with justification
- **finalization -> complete**: Document polished, checklist finalized, references complete

## Workflow

### Step 1: Initialize or Load State

Read the state file at `{research_dir}/{project}/state.md`.

**If project directory does not exist** and `topic` is provided:
1. Create directory structure: `{project}/`, `{project}/sessions/`, `{project}/sources/`, `{project}/artifacts/`
2. Initialize `state.md` using the state template with the given `topic`
3. Initialize `solution.md` using the solution template
4. Initialize `checklist.md` using the checklist template
5. Initialize `research-todo.md` with initial research items derived from the topic
6. Set phase to `discovery`, status to `in_progress`

**Initial TODO generation**: Based on the research topic, generate concrete research items for the discovery phase:
- Key concepts and technologies to understand
- Candidate solutions to investigate
- Comparison dimensions to define
- Known unknowns to explore

**If project directory does not exist** and `topic` is not provided:
- Report error: "Project '{project}' not found and no topic provided for initialization"
- Stop execution

**If project exists**: Read and parse `state.md` to determine current phase, status, and next action.

### Step 2: Plan This Session

**First, read `research-todo.md`** to understand the full research roadmap and current progress. This is the relay baton from previous sessions.

Based on the TODO, current phase, and `next_action` from state:
1. List items completed in previous sessions — don't redo them
2. Identify the top-priority pending items — these drive this session's focus
3. Check open questions — resolve any blockers before proceeding
4. Create a session plan covering:
   - What specific research questions to address (from pending TODO items)
   - What sources to investigate
   - What sections of the solution to work on
   - If `focus` parameter is provided, narrow the scope accordingly
   - Consider `max_depth` to limit how deep to go

Write the session plan as a brief outline (do not save to file yet).

### Step 3: Execute Research

Perform research using available tools (WebSearch, web page reading, etc.) based on the current phase:

**discovery**:
- Search for sources related to the research topic
- Use WebSearch with multiple query variations
- Read key web pages and documents
- Identify key themes, stakeholders, and knowledge gaps
- Save source summaries to `sources/source-{NNN}.md` files
- Each source file should contain: title, URL, date found, key points, relevance rating

**analysis**:
- Read all collected sources from `sources/` directory
- Synthesize findings, identify patterns and contradictions
- **Build a comparison matrix** of candidate solutions (see below)
- Evaluate evidence quality, benchmark data, and production usage
- Create analysis artifacts in `artifacts/` (comparison tables, trade-off matrices, scoring grids)
- Score candidates against evaluation criteria
- Identify the recommended approach with justification

**solution_draft**:
- Based on analysis results, draft solution document sections
- Write concrete, actionable content (not generic descriptions)
- Include specific technologies, steps, timelines, and metrics where applicable
- Update `solution.md` with new sections (read existing content first, merge carefully)
- Add references to supporting sources

**validation**:
- Review the draft solution against `checklist.md`
- Search for additional evidence to support or challenge key claims
- Test assumptions by finding counter-examples or alternative viewpoints
- Identify risks, edge cases, and potential failure modes
- Update checklist items as validated or needing revision

**finalization**:
- Polish solution document for clarity, consistency, and completeness
- Ensure all technical terms are defined
- Verify all references are complete and accessible
- Finalize the verification checklist with concrete, executable steps
- Add implementation priority and effort estimates

### Step 4: Assess Phase Progress

After research execution, honestly assess whether the current phase's objectives are met:
- Has enough information been gathered? (discovery)
- Are patterns identified and approaches compared? (analysis)
- Are all solution sections drafted with substance? (solution_draft)
- Are claims validated and risks identified? (validation)
- Is the document polished and complete? (finalization)

Update confidence level (0-100%) for the current phase.

### Step 5: Update Solution Document

Read the existing `solution.md` first, then update it:
- **Never overwrite** existing content without reading first
- Add new sections or expand existing ones
- Mark sections with `<!-- TODO -->` if they need more work in future sessions
- Update the References section with new sources found this session

### Step 6: Update Checklist

Read the existing `checklist.md` and update it:
- Add new verification items discovered during research
- Check off items that have been validated (change `- [ ]` to `- [x]`)
- Add concrete executable steps for verification
- Remove items that are no longer relevant

### Step 6.5: Update Research TODO

Read the existing `research-todo.md` and update it:
- Move completed items from "In Progress" or "Pending" to "Completed" with findings
- Update "In Progress" items with current state
- Add newly discovered research items to "Pending" (with priority ordering)
- Update "Open Questions" — resolve answered ones, add new ones
- Add any key decisions made this session to "Key Decisions Made"
- **This is critical**: the TODO is the relay baton for the next session

Create a timestamped session log file at `sessions/{YYYY-MM-DD_HHMMSS}.md`:

```markdown
# Session Log: {timestamp}

## Phase: {current_phase}
## Focus: {what was focused on this session}

## Actions Taken
- Searched for {query}
- Read {source_name}
- Analyzed {topic}
- Drafted {section_name}

## Key Findings
- Finding 1...
- Finding 2...

## Output Artifacts
- Updated solution.md section: {section}
- Created artifact: {filename}
- Validated checklist items: {N}

## Assessment
- Confidence: {X}%
- Phase transition: {yes/no and why}

## Next Steps
- [ ] Specific action for next session
- [ ] Another specific action
```

### Step 8: Update State

Rewrite `state.md` with updated information:
- Increment `total_sessions` by 1
- Update `last_updated` timestamp
- Update current phase (if transitioned)
- Update confidence percentage
- Update phase history with this session's summary
- Set `next_action` to a specific, actionable instruction for the next session

### Step 9: Save Artifacts

Save any intermediate artifacts created during research:
- Analysis notes, comparison tables, trade-off matrices go in `artifacts/`
- Source summaries go in `sources/`
- Use descriptive filenames: `analysis-{topic-slug}.md`, `comparison-{A}-vs-{B}.md`

### Step 10: Generate Report

Write a brief session summary report to `report_path` (injected by runner):

```markdown
# Research Session Report: {project}

## Topic: {topic}
## Phase: {current_phase} (Session #{N})
## Date: {timestamp}

## Progress This Session
{2-3 sentence summary of what was accomplished}

## Key Findings
- Finding 1
- Finding 2
- Finding 3

## Solution Progress
{Brief description of how the solution document advanced}

## Next Session Plan
{What the next scheduled session should focus on}
```

## Output Language

- All content: Chinese (中文) by default
- Technical terms: Keep English in parentheses after Chinese translation
- Source titles and URLs: Preserve original language
- Code and commands: Keep in English

## Important Notes

- **Stateless between sessions**: All context comes from state files. The skill must be able to pick up from any state.
- **Incremental progress**: Each session should make meaningful progress, even if small.
- **Honest assessment**: Don't inflate confidence levels. If research reveals the approach is flawed, say so.
- **Concrete and actionable**: Solution content should be specific enough to execute, not generic advice.
- **Source tracking**: Always save source summaries so future sessions can build on them.
