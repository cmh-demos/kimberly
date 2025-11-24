# Workflow and Projects

## GitHub Projects

This repository uses GitHub Projects for issue tracking and sprint planning.

### Board Structure

- **Backlog**: Unprioritized features and bugs.
- **In Progress**: Currently worked on items (max 3 per person).
- **Review**: Items awaiting code review or testing.
- **Done**: Completed items, ready for release.

### Sample Cards

- **Card: Implement basic chat** - Backlog
  - Description: Add conversational interface.
  - Labels: feature, MVP
  - Assignee: @developer

- **Card: Memory management** - In Progress
  - Description: Implement short-term memory.
  - Labels: core, memory

## Automation

- Auto-move to Review on PR open.
- Auto-close on merge to main.

## Workflow Process for Work Management in Kimberly Project

This document outlines the standardized process for managing work items in the Kimberly project, from creation to completion. It ensures consistency, accountability, and alignment with project goals. All work is tracked via GitHub issues using the work-tracking template.

### 1. Creating Work

Work items (e.g., features, bugs, tasks, epics) are identified and documented as GitHub issues.

#### Steps

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

#### Responsible Roles

- Product Manager (PM) for feature requests and prioritization.
- Engineering Lead or QA for bugs/tasks.
- Any team member for documentation or minor tasks.

### 2. Assigning Work

Every issue must be assigned to someone from the roles list in `roles.md` to ensure accountability.

#### Steps

- **Review and Prioritize**: In weekly sync or sprint planning meetings, review open issues. Prioritize based on backlog and sprint goals.
- **Match to Roles**: Assign based on responsibilities in `roles.md` (e.g., Backend Developer for API tasks, SRE for infra issues).
- **Update Issue**: Set the assignee in GitHub. If multiple roles are needed, assign to the primary owner and note collaborators in comments.
- **Communicate**: Notify the assignee via issue comments or meetings. Ensure they acknowledge and understand the work.

#### Responsible Roles

- Product Manager (PM) for prioritization and high-level assignment.
- Engineering Lead for technical assignments and coordination.

### 3. Tracking Work

Work progress is monitored through GitHub issues, project boards, and meetings.

#### Steps

- **Update Status**: Assignees update the issue with progress (e.g., add comments, link PRs, update acceptance criteria checkboxes).
- **Project Board**: Move issues across columns (e.g., Backlog → In Progress → Done) in `docs/project-board.md` or GitHub Projects.
- **Meetings**: Discuss progress in weekly syncs, bi-weekly grooming, or sprint retros. Report blockers, risks, and adjustments.
- **Metrics**: Track against KPIs (e.g., latency, coverage) and update estimates if needed.
- **Dependencies**: Note any dependencies on other issues or external factors.

### 4. Completing Work

Work is considered complete when it meets the Definition of Done (DoD) in `docs/DEFINITION_OF_DONE.md`.

#### Steps

- **Self-Review**: Assignees verify against DoD criteria (code quality, testing, functionality, documentation, security).
- **Submit for Review**: Create PR and request reviews from required reviewers (see reviewer matrix in CONTRIBUTING.md).
- **Address Feedback**: Iterate on PR comments until approved.
- **Merge and Deploy**: Merge to main after CI passes; deploy to staging/production.
- **Close Issue**: Mark issue as done; update project board.
- **Retrospective**: In sprint retro, discuss what went well and improvements for future work.

#### Responsible Roles

- Assignees for implementation and self-review.
- Reviewers for quality checks.
- QA for final validation.

### 5. Maintenance and Continuous Improvement

Ongoing activities to keep the process effective.

#### Steps

- **Monitor Metrics**: Track cycle time, throughput, and quality metrics.
- **Process Reviews**: Quarterly reviews of the workflow process; update based on feedback.
- **Tool Updates**: Keep GitHub Projects, issue templates, and automation up-to-date.
- **Training**: Onboard new team members on the process.

#### Responsible Roles

- Engineering Lead for process oversight.
- Team for feedback and participation.

## Software Development Lifecycle (SDLC)

This document describes the Software Development Lifecycle (SDLC) for the Kimberly project, ensuring structured, iterative development with quality and collaboration.

### Overview

Kimberly follows an Agile-inspired SDLC with phases: Planning, Design, Development, Testing, Deployment, and Maintenance. Iterations are 2-week sprints.

### Phases

#### 1. Planning

- **Activities**:
  - Backlog grooming: Prioritize features/bugs from needs-work.md and issues.
  - Sprint planning: Select items, estimate effort (story points), assign owners.
  - Risk assessment: Review RISK_ANALYSIS.md.
- **Artifacts**: Sprint backlog, acceptance criteria.
- **Roles**: PM, Engineering Lead, Team.
- **Duration**: 1-2 days per sprint.

#### 2. Design

- **Activities**:
  - Architecture design: Update ARCHITECTURE.md, create diagrams.
  - API design: Update openapi.yaml.
  - UI/UX: Wireframes, mocks (see wireframes/README.md).
  - Security review: Threat modeling.
- **Artifacts**: Design docs, ADRs.
- **Roles**: Engineering Lead, UI/UX Designer, Security Engineer.
- **Duration**: As needed per feature.

#### 3. Development

- **Activities**:
  - Code implementation: Follow CODING_STANDARDS.md.
  - Pair/mob programming for complex features.
  - Daily stand-ups: Progress updates.
  - Branching: Feature branches (e.g., `feat/add-chat-api`).
- **Artifacts**: Code commits, unit tests.
- **Roles**: Developers (Backend, Frontend, etc.).
- **Duration**: Bulk of sprint.

#### 4. Testing

- **Activities**:
  - Unit/integration testing: 95% coverage.
  - QA testing: Manual/E2E.
  - Security testing: Scans, reviews.
  - Performance testing: Benchmarks.
- **Artifacts**: Test reports, bug fixes.
- **Roles**: QA Engineer, Developers.
- **Duration**: Ongoing; final validation before release.

#### 5. Deployment

- **Activities**:
  - CI/CD: Automated builds/tests via GitHub Actions.
  - Staging deployment: Test in staging environment.
  - Production release: Gradual rollout (e.g., canary).
  - Monitoring: Post-deploy checks.
- **Artifacts**: Release notes, CHANGELOG.md updates.
- **Roles**: DevOps Engineer, SRE.
- **Duration**: 1-2 days.

#### 6. Maintenance

- **Activities**:
  - Bug fixes, patches.
  - Monitoring: Logs, metrics (Prometheus/Grafana).
  - User feedback: Incorporate into backlog.
  - Retrospectives: Improve process.
- **Artifacts**: Hotfixes, metrics reports.
- **Roles**: All team.
- **Duration**: Continuous.

### Tools and Automation

- **Version Control**: Git (GitHub).
- **CI/CD**: GitHub Actions (linting, tests, deployment).
- **Project Management**: GitHub Issues/Projects.
- **Communication**: GitHub Discussions, meetings.
- **Documentation**: Markdown files, auto-generated API docs.

### Quality Gates

- **Code Review**: Required for all PRs; checklist in CONTRIBUTING.md.
- **CI Checks**: Must pass (lint, test, coverage).
- **Security Review**: For sensitive features.
- **Acceptance**: Meets criteria in sprint-plan.md.

### Metrics and Improvement

- **KPIs**: Cycle time, defect rate, deployment frequency.
- **Retros**: End-of-sprint; update process.
- **Continuous Improvement**: Adopt new tools/practices as needed.

### Compliance and Ethics

- **Legal**: Adhere to open-source licenses, data privacy (GDPR).
- **Ethics**: Bias-free AI, user consent.
- **Security**: Regular audits.

For role details, see roles.md. Questions? See CONTRIBUTING.md.
