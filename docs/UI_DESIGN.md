# Kimberly — UX / UI Design Proposal

## Overview

A web-first, privacy-forward UI for Kimberly, the local-friendly personal AI assistant. This document summarizes the interface strategy, primary users, key flows, major screens, UI components, accessibility guidance, and next steps for prototypes.

## Design goals

- Keep chat low-friction and explainable.
- Make memory controls visible and understandable (tiered quotas, protect/archive/delete).
- Provide developer/power-user tooling for agents, manual mediation runs, and metrics without exposing sensitive internals to consumers.

## Primary users

- Non-technical end users: chat, control privacy, manage a small set of memories.
- Power users: explore memory manager, run agents, trigger mediation, export/purge data.
- Hosts/administrators: configure local embedding options and quotas.

## Top-level screens

1. Chat — main conversational surface with context toggle and context preview panel.
2. Memory Manager — filterable list, quota visualization, memory detail and bulk actions.
3. Agents Dashboard — discover, configure, and run agents; show agent logs and effects.
4. Metrics & Health — per-user storage, meditation history, usage trends.
5. Settings & Privacy — quotas, export/purge, consent, embedding opt-in (self-hosted only).

## Key interaction patterns

- Context transparency: each time a memory is included in a prompt, show a small explanation (“included because it matches your goal: 'project X' — score 0.79”) with a quick remove button.
- Save-to-memory explicit: messages are not saved by default; provide clear opt-in when saving memories from chat.
- Sandbox agents: require explicit sandbox toggle for agents that modify memory; always show a summary of memory reads/writes before committing.
- Quota visibility: a small persistent quota bar (short | long | permanent) with hover/tooltips explaining thresholds and actions to remediate.

## Accessibility

- Target: WCAG 2.1 AA. Semantic HTML, keyboard-first interaction, annoucement to screen readers when memory is saved/removed, and voice controls must include captions.

## Deliverables & next steps

1. Low-fidelity wireframes for Chat, Memory Manager, and Agents (desktop and mobile).
2. High-fidelity mockups and a simple interactive prototype (Figma or static HTML/CSS).
3. Accessibility checklist and test plan (WCAG items + keyboard/voice tests).

## Owner / contact

Design owner: <product-design@kimberly.local> (placeholder)

## Notes

This proposal focuses on making memory and privacy transparent to users while keeping a lightweight UI that can be extended to mobile and voice surfaces.
