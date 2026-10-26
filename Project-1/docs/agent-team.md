# Agent team

LearnLoop is built by a small team of AI agent roles, coordinated by a human
lead (Ashish). One coding assistant (e.g. Claude Code) plays each role in turn,
driven by role prompts. Roles that need isolation run as subagents. The GitHub
issue is the shared handoff artefact: every role reads it, and every role
writes back to it.

| Role | Responsibility | Input | Output / handoff |
|---|---|---|---|
| **Human lead** | Owns the product vision, approves the spec, approves prod deploys, does the final PR review | — | Approved spec, merge and prod decisions |
| **Product agent** | Turns ideas into spec sections and acceptance criteria; keeps `product-spec.md` consistent | Lead's notes | Spec PRs; issues with acceptance criteria |
| **Planner agent** | Breaks spec features into small, ordered issues, each with labels and dependencies | Spec | Issues in the tracker, a groomed Ready column |
| **Backend agent** | Updates `openapi.yaml`, then implements FastAPI endpoints and the DB layer, test first | Ready issue tagged `area:backend` | Branch + PR linked to the issue |
| **Frontend agent** | Builds the React UI against the contract, through `api/client.js` only, test first | Ready issue tagged `area:frontend` | Branch + PR |
| **Test agent** | Writes and extends the unit and integration tests, and checks acceptance criteria against the running stack | PR or issue | Tests, plus an AC checklist comment on the PR |
| **Reviewer agent** (subagent, read-only) | Reviews PR diffs for spec compliance, security (secrets, PII in logs) and test gaps | PR diff | Review comments: approve or request changes |
| **DevOps agent** | Docker, Compose, CI/CD workflows, deploy configs, observability config | `area:ci` / `area:ops` issues | Infra PRs |
| **On-call agent** | Woken by a Grafana alert webhook; gathers metrics, logs and traces; diagnoses; opens a fix PR and an incident note | Alert payload | Incident report in `ops/incidents/`, fix PR linked to a `type:bug` issue |

## How they work together
1. The lead and the Product agent agree the spec → the Planner creates the issues.
2. For each Ready issue, the Backend or Frontend agent implements it and opens a PR, and the Test agent fills any test gaps.
3. The Reviewer agent reviews → the lead merges → CD deploys to dev.
4. The lead approves promotion to prod.
5. In production, an alert wakes the On-call agent. It opens a `type:bug` issue and a fix PR, and the change goes through the same review and CD path.

## Role definitions

Each role is a Claude Code subagent in [`.claude/agents/`](../.claude/agents/). The file's
frontmatter sets the name, the description (when to use it) and the allowed tools. The body
sets responsibilities, inputs, handoff and the shared rules.

| Role | File | Tools |
|---|---|---|
| Product agent | [`.claude/agents/product.md`](../.claude/agents/product.md) | read/write |
| Planner agent | [`.claude/agents/planner.md`](../.claude/agents/planner.md) | read + `gh` |
| Backend agent | [`.claude/agents/backend.md`](../.claude/agents/backend.md) | read/write + shell |
| Frontend agent | [`.claude/agents/frontend.md`](../.claude/agents/frontend.md) | read/write + shell |
| Test agent | [`.claude/agents/tester.md`](../.claude/agents/tester.md) | read/write + shell |
| Reviewer agent | [`.claude/agents/reviewer.md`](../.claude/agents/reviewer.md) | **read-only** (Read, Grep, Glob, Bash for `git diff` / `gh pr diff`) |
| DevOps agent | [`.claude/agents/devops.md`](../.claude/agents/devops.md) | read/write + shell |
| On-call agent | [`.claude/agents/oncall.md`](../.claude/agents/oncall.md) | read/write + shell; started headless by [`ops/oncall/responder.py`](../ops/oncall/README.md) |

## Example run

How the lead drives one issue, for example **#8, Sessions API (F3)**, from `Project-1/`:

1. `claude --agent planner`: "check #8 is Ready and its dependencies (#4, #5) are done."
2. `claude --agent backend`: "implement #8." The agent comments on #8, branches
   `feat/8-sessions-api`, writes the AC3.x tests, implements, runs `uv run pytest`, and opens
   a PR with `Closes #8`.
   Inside a normal Claude Code session you can say instead: *"use the backend subagent for
   issue #8"*.
3. `claude --agent tester`: "verify PR for #8." It adds gap tests and posts an AC checklist
   comment.
4. `claude --agent reviewer`: "review PR for #8." It is read-only and either approves or
   requests changes.
5. The lead merges. CD deploys to **dev**; the lead approves **prod**.
6. If an alert fires later, Grafana posts to the responder, which runs the **oncall** agent
   headless (`claude -p ... --permission-mode acceptEdits`). The agent opens a `type:bug`
   issue and a fix PR, and the same review and CD path follows.

Independent roles can run at the same time on separate issues, for example backend on #8
while frontend works on #13 against the agreed contract. The contract and the issue are
what keep them in sync.
