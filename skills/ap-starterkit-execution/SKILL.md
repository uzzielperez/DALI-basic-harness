---
name: ap-starterkit-execution
description: Executes the LHCb Analysis Productions Starterkit workflow step-by-step with command validation, environment checks, local lb-ap testing, and MR preparation guidance. Use when the user asks to run or troubleshoot Starterkit Analysis Productions steps, create starterkit info.yaml jobs, validate with lb-ap, or prepare a practice MR.
---

# AP Starterkit Execution Assistant

Use this skill to guide and execute the Starterkit Analysis Productions workflow in a robust order.

## Scope

- Environment checks (`lb-ap`, proxy/auth readiness)
- Starterkit production scaffolding (`starterkit/` files)
- `lb-ap` validation and local test execution
- Commit/MR preparation and CI follow-up guidance

## Default behavior

1. Execute in small verified steps.
2. Show exact command(s) used and key outputs.
3. Stop and explain clearly on first failing step.
4. Propose fix, then continue after user confirmation for sensitive actions.

## Sensitive actions (always confirm first)

- Pushing to remote branches
- Opening or updating merge requests
- Any action requiring token/credential setup

