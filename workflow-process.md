# Workflow Process for Work Management in Kimberly Project

This document outlines the standardized process for managing work items in the Kimberly project, from creation to completion. It ensures consistency, accountability, and alignment with project goals. All work is tracked via GitHub issues using the work-tracking template.

## 1. Creating Work

Work items (e.g., features, bugs, tasks, epics) are identified and documented as GitHub issues.

### Steps:
- **Identify the Need**: Work can originate from backlog grooming, sprint planning, user feedback, bugs, or PM/product decisions. Reference docs like `docs/backlog-next-3-sprints.md` or `docs/project-board.md`.
- **Create the Issue**: Use the work-tracking issue template (`.github/ISSUE_TEMPLATE/work-tracking.md`). Fill in all required fields:
  - Issue Type (e.g., Bug, Feature Request).
  - Priority (Critical, High, Medium, Low).
  - Description (clear, concise, with context).
  - Acceptance Criteria (checklist of completion requirements).
  - Estimation (rough time in days or story points).
  - Related Documents/Links (e.g., link to relevant docs or PRDs).
- **Add Labels**: Apply appropriate labels (e.g., "backend", "frontend", "bug") in addition to "work-tracking".
- **Initial Triage**: If not immediately assignable, leave assignee blank for review in the next meeting.

### Responsible Roles:
- Product Manager (PM) for feature requests and prioritization.
- Engineering Lead or QA for bugs/tasks.
- Any team member for documentation or minor tasks.

## 2. Assigning Work

Every issue must be assigned to someone from the roles list in `roles.md` to ensure accountability.

### Steps:
- **Review and Prioritize**: In weekly sync or sprint planning meetings, review open issues. Prioritize based on backlog and sprint goals.
- **Match to Roles**: Assign based on responsibilities in `roles.md` (e.g., Backend Developer for API tasks, SRE for infra issues).
- **Update Issue**: Set the assignee in GitHub. If multiple roles are needed, assign to the primary owner and note collaborators in comments.
- **Communicate**: Notify the assignee via issue comments or meetings. Ensure they acknowledge and understand the work.

### Responsible Roles:
- Product Manager (PM) for prioritization and high-level assignment.
- Engineering Lead for technical assignments and coordination.

## 3. Tracking Work

Work progress is monitored through GitHub issues, project boards, and meetings.

### Steps:
- **Update Status**: Assignees update the issue with progress (e.g., add comments, link PRs, update acceptance criteria checkboxes).
- **Project Board**: Move issues across columns (e.g., Backlog → In Progress → Done) in `docs/project-board.md` or GitHub Projects.
- **Meetings**: Discuss progress in weekly syncs, bi-weekly grooming, or sprint retros. Report blockers, risks, and adjustments.
- **Metrics**: Track against KPIs (e.g., latency, coverage) and update estimates if needed.
- **Dependencies**: Note any dependencies on other issues or external factors.

### Responsible Roles:
- Assignee for daily updates.
- Product Manager (PM) for overall tracking and reporting.
- Engineering Lead for technical progress oversight.

## 4. Completing Work

Work is marked complete when acceptance criteria are met and code is ready for review.

### Steps:
- **Implement and Test**: Develop the feature/bug fix, write tests, and ensure it meets acceptance criteria.
- **Code Review**: Submit a PR, get reviews from relevant roles (e.g., Backend Developer reviews backend code).
- **Merge and Deploy**: After approval, merge to main branch. Ensure CI passes and deployment succeeds.
- **Update Issue**: Mark acceptance criteria as complete. Add "Actual Time Spent" field with the real time taken.
- **Documentation**: Update docs if needed (e.g., API changes in `docs/API.md`).

### Responsible Roles:
- Assignee for implementation and PR.
- QA Engineer for testing and validation.
- SRE/DevOps for deployment.
- Documentation Engineer for doc updates.

## 5. Verifying Work Completion

Completion is verified through testing, reviews, and retrospectives to ensure quality and alignment.

### Steps:
- **Automated Checks**: Ensure CI passes (e.g., tests, linting, OpenAPI validation).
- **Manual Verification**: QA performs E2E tests, smoke tests, and validates against acceptance criteria.
- **Stakeholder Review**: In sprint retros or demos, confirm the work meets requirements and doesn't introduce regressions.
- **Close Issue**: Once verified, close the issue. Add retrospective notes (e.g., what went well, lessons learned).
- **Update Metrics**: Log actual time for future estimation accuracy. Update project board and reports.

### Responsible Roles:
- QA Engineer for testing and verification.
- Product Manager (PM) for acceptance and stakeholder sign-off.
- Engineering Lead for technical validation.

## General Guidelines
- **Time Tracking**: Every issue must have an estimate at creation and actual time at completion for process improvement.
- **Roles Reference**: Always assign from `roles.md` to match skills and responsibilities.
- **Communication**: Use issue comments for updates; escalate blockers in meetings.
- **Quality Gates**: No work is complete without meeting acceptance criteria, passing tests, and code review.
- **Continuous Improvement**: Use retros to refine this process (e.g., adjust estimates, improve templates).

This process promotes transparency, efficiency, and high-quality delivery for the Kimberly project.