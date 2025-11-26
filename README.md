# Kimberly

Kimberly is a personal AI assistant inspired by Jarvis from Iron Man. It supports
conversational interaction across multiple platforms and provides advanced memory
management and agent delegation for seamless task handling.

## Features

## Overview

Kimberly focuses on delivering a natural conversational experience across web, voice,
and mobile. The design prioritizes memory accuracy, privacy, and small resource
footprints so it can run in constrained environments when required.

## Core Features

### Conversational Interface

- Natural language chat with voice, web, and mobile support.
- Multi-platform availability:
  - Voice (e.g., smart speakers)
  - Web (browser-based)
  - Mobile (iOS/Android apps)
- Real-time responses with context awareness.

### Memory Management

- See `docs/memory-model.md` for canonical definitions of:
  - short-term, long-term, and permanent memory tiers
  - quotas, meditation, and retention policies
- (Avoid duplicating quota numbers in multiple docs; refer to the canonical source.)
**Meditation**: Nightly grading of memories using a weighted score.

- Weights (example):

- 40% relevance to goals
- 30% emotional weight
- 20% predictive usefulness
- 10% recency/frequency

Memories below the configured threshold are forgotten.

### Agent Delegation

- Offloads tasks to specialized agents for efficiency.
- Core Agents:
  - **Scheduler**: Manages calendar, reminders, and task planning.
Integrates with external calendars.
  - **Researcher**: Handles web searches, data gathering, and summarization.
  - **Coder**: Assists with code writing, debugging, and automation.
  - **Reminder**: Tracks follow-ups, deadlines, and notifications.
- Limits: Max 3 concurrent agents, resource-capped to prevent overload.

### Learning and Adaptation

- **Interaction logging**: Stores conversations in short, long, and permanent
memory and analyzes patterns such as preferences and habits.
- **User feedback**: Explicit corrections (for example, "no, I meant X") or ratings
adjust responses.
- **Reinforcement**: Positive outcomes (for example, successful task completion)
reinforce similar behaviors. Meditation grades are used to refine and improve memory
prioritization based on relevance and emotional signals.
- **Agent insights**: Delegates learning to agents (for example, Researcher learns
from web data; Coder learns from code patterns).

This builds a personalized model over time.

## Future Enhancements

- Seamless agent integration.
- Advanced personalization based on memory.
- Expanded platform support.
- Offline mode for basic functions without internet.
- Custom plugins for user-extensible agents/modules.
- Integrations with GitHub, Slack, and email for seamless workflows.
- Advanced NLP with sentiment analysis and multi-language support.
- UI customization including themes, voice tones, and personalized avatars.
- AR/VR integration for immersive interfaces.
- Blockchain data integrity for secure memory logs.
- Gamification with rewards/badges for consistent use.
- Health monitoring integration with wearables.
- Predictive actions to anticipate user needs.
- Emergency mode for priority handling of urgent requests.
- External learning from public knowledge bases.
- Multi-modal input support for images, videos, and audio.

## Documentation

- **Technical Docs**: Core docs like memory model and API specs are in `docs/`.
- **Project Wiki**: For planning, roadmaps, and collaborative docs, visit the
[GitHub Wiki](https://github.com/cmh-demos/kimberly/wiki).

## Installation

1. Clone the repository: `git clone https://github.com/cmh-demos/kimberly.git`
2. Navigate to the directory: `cd kimberly`
3. Create and activate virtual environment: `python -m venv .venv && source
   .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

If you only need to run the grooming scripts (for example
`scripts/grooming_runner.py`) or lightweight developer tooling, use the
minimal requirements file to avoid heavy ML packages (e.g., PyTorch,
transformers) which are large and slow to download:

```bash
pip install -r requirements-groomer.txt
```

The top-level `requirements.txt` includes ML frameworks (torch,
transformers, accelerate) that pull very large binary wheels (hundreds
of MB each) and additional NVIDIA libraries — these are the primary
reason installs can take a long time or use a lot of disk space.

## Quickstart

1. Run the app: `python app.py`
2. The API will be available at <http://localhost:8000>

### Example Usage

Send a chat message:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Kimberly!"}'
```

Expected response:

```json
{
  "response": "Hello, Kimberly! How can I help you today?"
}
```

### Environment Variables

- None required for minimal setup. For production, configure model paths,
API keys, and other environment variables as needed.

## Risk analysis

We track project risks and open investigation items in `docs/RISK_ANALYSIS.md` — a
living register with prioritized risks, mitigations, and the list of unknowns we still
need to resolve. Please review it before making architecture or policy decisions.

## Usage

- Start chat: Interact via web interface or API.
- Voice: Use smart speaker integration.
- Mobile: iOS and Android apps are planned for a future release.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is proprietary. All rights reserved.

See the [LICENSE](LICENSE) file for details. No permission is granted for use,
modification, or distribution without explicit written consent from the copyright
holder.
