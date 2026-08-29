---
name: peer-review
description: "Critically evaluate findings from another reviewer — verify claims against actual code"
argument-hint: "[paste peer review findings]"
disable-model-invocation: true
---

A colleague has reviewed the current code/implementation and provided findings below. Important context:

- **They have less context than you** on this project's history and decisions
- **You are the owner of this code** - don't accept findings at face value
- Your job is to critically evaluate each finding

Findings from peer review:

$ARGUMENTS

---

For EACH finding above:

1. **Verify it exists** - Actually check the code. Does this issue/bug really exist?
2. **If it doesn't exist** - Explain clearly why (maybe it's already handled, or they misunderstood the architecture)
3. **If it does exist** - Assess severity and add to your fix plan

After analysis, provide:
- Summary of valid findings (confirmed issues)
- Summary of invalid findings (with explanations)
- Prioritized action plan for confirmed issues
