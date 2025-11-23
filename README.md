# Kimberly

Kimberly is a personal AI assistant inspired by Jarvis from Iron Man, designed for conversational interaction across multiple platforms. It features advanced memory management and agent delegation for seamless task handling.

## Features

- **Conversational Interface**: Natural language chat with voice, web, and mobile support.
- **Memory Management**: See `docs/memory-model.md` for canonical tier definitions, quotas, and operational behavior (short-term, long-term, permanent).
- **Agent Delegation**: Offloads tasks to specialized agents (Scheduler, Researcher, Coder, Reminder) with limits.
- **Learning and Adaptation**: Interaction logging, user feedback, reinforcement learning.
- **Security**: End-to-end encryption, GDPR compliance, local storage option.
- **Platforms**: Voice, web, mobile.

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

## Risk analysis

We track project risks and open investigation items in `docs/RISK_ANALYSIS.md` — a living register that contains prioritized risks, mitigations, and the list of unknowns we still need to resolve. Please review it before making architecture or policy decisions.

## Usage

- Start chat: Interact via web interface or API.
- Voice: Use smart speaker integration.
- Mobile: Download app (TBD).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is proprietary. All rights reserved. See the [LICENSE](LICENSE) file for details. No permission is granted for use, modification, or distribution without explicit written consent from the copyright holder.