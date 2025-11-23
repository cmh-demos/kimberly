# Kimberly

Kimberly is a personal AI assistant inspired by Jarvis from Iron Man, designed for conversational interaction across multiple platforms. It features advanced memory management and agent delegation for seamless task handling.

## Core Features

### Conversational Interface
- Natural language chat with voice, web, and mobile support.
- Multi-platform availability: Voice (e.g., smart speakers), Web (browser-based), Mobile (iOS/Android apps).
- Real-time responses with context awareness.

### Memory Management
- See `docs/memory-model.md` for canonical definitions of short-term, long-term, and permanent memory tiers, quotas, meditation, and retention policies.
- (Avoid duplicating quota numbers in multiple docs; refer to the canonical source.)
- **Meditation**: Nightly grading of memories using a weighted score (40% relevance to goals, 30% emotional weight, 20% predictive usefulness, 10% recency/frequency). Memories below threshold are forgotten.

### Agent Delegation
- Offloads tasks to specialized agents for efficiency.
- Core Agents:
  - **Scheduler**: Manages calendar, reminders, and task planning (integrates with external calendars).
  - **Researcher**: Handles web searches, data gathering, and summarization.
  - **Coder**: Assists with code writing, debugging, and automation.
  - **Reminder**: Tracks follow-ups, deadlines, and notifications.
- Limits: Max 3 concurrent agents, resource-capped to prevent overload.
### Learning and Adaptation
- **Interaction logging**: Stores conversations in short/long/permanent memory, analyzing patterns (e.g., preferences, habits).
- **User feedback**: Explicit corrections (e.g., "no, I meant X") or ratings adjust responses.
- **Reinforcement**: Positive outcomes (e.g., successful task completion) boost similar behaviors; meditation grades and refines based on relevance/emotion.
- **Agent insights**: Delegates learning to agents (e.g., Researcher learns from web data, Coder from code patterns).

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
- **Project Wiki**: For planning, roadmaps, and collaborative docs, visit the [GitHub Wiki](https://github.com/cmh-demos/kimberly/wiki).

## Installation

1. Clone the repository: `git clone https://github.com/cmh-demos/kimberly.git`
2. Navigate to the directory: `cd kimberly`
3. Create and activate virtual environment: `python -m venv .venv && source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Quickstart

1. Run the app: `python app.py`
2. The API will be available at http://localhost:8000

### Example Usage

Send a chat message:

```bash
curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d '{"message": "Hello, Kimberly!"}'
```

Expected response:
```json
{"response": "Hello, Kimberly! How can I help you today?"}
```

### Environment Variables

- None required for minimal setup. For production, configure model paths, API keys, etc.

## Security and Risks

We track project risks and open investigation items in `SECURITY_AND_RISKS.md` — a living register that contains prioritized risks, mitigations, and the list of unknowns we still need to resolve. Please review it before making architecture or policy decisions.

## Usage

- Start chat: Interact via web interface or API.
- Voice: Use smart speaker integration.
- Mobile: Access via Progressive Web App (PWA) - installable on iOS and Android devices.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is proprietary. All rights reserved. See the [LICENSE](LICENSE) file for details. No permission is granted for use, modification, or distribution without explicit written consent from the copyright holder.