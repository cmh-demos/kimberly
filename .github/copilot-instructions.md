# Custom instructions for Copilot

## Coding style

prefer snake_case unless it conflicts with linting rules or established conventions in a specific context.

## Indentation

prefer 2 spaces for indentation in all files.

## Line length

prefer a maximum line length of 80 characters.

## Code Review

- Prioritize clear, readable code and maintainable solutions.
- Avoid unnecessary complexity and premature optimization.

## General Preferences

- Do not request 
- Prefer to have all questions answered before proceeding with code generation.
- When generating code, include comments to explain complex logic or decisions.

## Local workspace overrides (VS Code only)

When running inside a local Visual Studio Code session, consult these local
files (in order) to *augment* repository guidance. The assistant should *not*
change repo-level policy autonomously — local overrides only influence
interactive suggestions in this VS Code session unless the user explicitly
accepts and commits edits.

Files to consult (search in this order):
  1. rules_for_copilot.yml

prefer venv when possible