# Design & Branding

This file consolidates UI/UX design and branding guidelines for Kimberly (previously `docs/UI_DESIGN.md` and `docs/BRANDING.md`). It covers goals, primary users, screens, accessibility, color palette, typography, logo usage, and visual assets.

## Overview
A web-first, privacy-forward UI for Kimberly, the local-friendly personal AI assistant. The design emphasizes low-friction chat, visible memory controls, clear sandboxing for agents, and accessible, inclusive interfaces.

## Design goals
- Keep chat low-friction and explainable.
- Make memory controls visible and understandable (tiered quotas, protect/archive/delete).
- Provide dev tooling for agents, mediation runs, and metrics without exposing internals to normal users.

## Primary users
- Non-technical end users: chat, control privacy, manage a small set of memories.
- Power users: memory manager, run agents, export/purge data.
- Hosts/administrators: configure local embedding options and quotas.

## Top-level screens
1. Chat — main conversational surface with context toggle and context preview panel.
2. Memory Manager — filterable list, quota visualization, memory detail and bulk actions.
3. Agents Dashboard — discover, configure, and run agents; show agent logs and effects.
4. Metrics & Health — per-user storage, meditation history, usage trends.
5. Settings & Privacy — quotas, export/purge, consent, embedding opt-in (self-hosted only).

## Accessibility
- Target: WCAG 2.1 AA. Semantic HTML, keyboard-first, screen reader announcements when memory changes, captions for voice controls.

---

## Branding Guidelines

Kimberly's brand embodies intelligence, trust, and personalization. The guidelines below define palette, typography, iconography and voice.

### Color Palette
- Primary: Deep Purple (#6A0DAD)
- Secondary: Lavender (#E6E6FA)
- Accent: Electric Indigo (#4B0082)
- Neutral: Light Grey (#F5F5F5) and Dark Grey (#333333)
- Success/Error: Green (#28A745) and Red (#DC3545)

### Typography
- Primary font: Roboto (sans-serif)
- Secondary font: Open Sans

### Logo & Iconography
- Primary logo: stylized "K" with neural patterns (see `docs/branding/logo.svg`)
- Icon: brain/memory icon (see `docs/branding/icon.svg`)
- Maintain clear spacing and minimum sizes; provide monochrome and small-icon variants.

### Voice & Messaging
- Tone: friendly, helpful, and professional. Use simple language, avoid jargon.
- Taglines and example messages should emphasize privacy-first intelligence and helpfulness.

### Platform Usage
- Web: deep purple for headlines and CTAs.
- Mobile: lavender backgrounds, electric indigo highlights.
- Voice: TTS tone should match brand voice; use short auditory cues for interactions.

## Assets & Files
- Visual assets are available in `docs/branding/` (icons, logos, swatches).

## Next steps
- Produce low- and high-fidelity mockups and check against WCAG tests.
- Integrate style tokens into frontend repo when ready.
