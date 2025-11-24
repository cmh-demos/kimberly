# Repository GitHub Project — how we run work

Purpose: provide a lightweight, consistent GitHub Projects setup and onboarding checklist for this repository.

Recommended board layout (columns)
- Backlog — all untriaged/unscheduled issues
- Selected for Development — planned for next sprint
- In progress — actively worked issues/PRs
- Review / QA — PRs and validation
- Done — Completed work

Labels (examples & suggested mapping)
- enhancement — feature requests
- bug — bug reports
- chore — maintenance / infra
- wip — short-lived work-in-progress
- needs-triage — newly filed issues needing review

Issue -> column rules (suggested)
- New issues: Backlog
- When groomed and prioritized: Selected for Development
- When assigned & started: In progress
- When PR opened or ready for validation: Review / QA
- After merge + validation: Done

Automation & tooling (no GH Actions required)
- Manual: Use GitHub Projects UI to create a Project (Kanban) and add columns above.
- CLI: Use the `gh` CLI to create a project and add columns (see below example).
- API: For programmatic builds, use the GitHub Projects API or infra/automation tooling external to repo.

CLI quick-start (optional, run locally or from a maintainer machine):

```bash
# create a project board
gh project create "Kimberly — Work" --body "Primary project board" --org=false
# add columns
gh project column create "Backlog" --project "Kimberly — Work"
gh project column create "Selected for Development" --project "Kimberly — Work"
gh project column create "In progress" --project "Kimberly — Work"
gh project column create "Review / QA" --project "Kimberly — Work"
gh project column create "Done" --project "Kimberly — Work"
```

Recommendations & next steps
- Add or sync a canonical label set (we prefer lightweight labels matching types in `rules_for_copilot.yml`).
- Create issue templates (already included) and a PR template (already included) to make onboarding consistent.
- If you want automation for moving issues <-> columns on PR events, we can discuss using either GitHub Automations (Projects v2), the GitHub API, or a small external microservice — we will not add GitHub Actions unless explicitly approved.

Onboarding (for new contributors)
1. Open issues using the templates in `.github/ISSUE_TEMPLATE/`.
2. Assign estimate and owner via comments and labels.
3. Move issues to `Selected for Development` during sprint planning.
4. Work, open PR, and move issue to `Review / QA`.
5. Once merged and validated, move to `Done`.
