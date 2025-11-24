# Kimberly Agents

A VS Code extension providing custom Copilot chat agents based on the roles defined in
the Kimberly project.

## Agents

This extension includes the following chat participants:

### Core Development Roles

- **@backend-developer**: Backend Developer agent for server-side logic and
API development
- **@frontend-developer**: Frontend Developer agent for user interfaces and
client-side applications
- **@engineering-lead**: Engineering Lead agent for technical architecture
and oversight

### Operations and Infrastructure Roles

- **@sre**: SRE agent for system reliability and operations
- **@devops-engineer**: DevOps Engineer agent for infrastructure and
deployment

### Quality and Testing Roles

- **@qa-engineer**: QA Engineer agent for software quality and testing

### Security and Compliance Roles

- **@security-engineer**: Security Engineer agent for threat protection and
secure implementation
- **@privacy-data-engineer**: Privacy/Data Engineer agent for data privacy and
compliance
- **@legal-advisor**: Legal Advisor agent for legal compliance and risk
mitigation

### Product and Design Roles

- **@product-manager**: Product Manager agent for product vision and delivery
- **@ui-ux-designer**: UI/UX Designer agent for user interfaces and
experiences
- **@branding-manager**: Branding Manager agent for brand identity and
management

### Specialized Roles

- **@ml-engineer**: ML Engineer agent for machine learning models and AI
integrations
- **@api-engineer**: API Engineer agent for API design and integration
- **@documentation-engineer**: Documentation Engineer agent for project
documentation

## Inter-Agent Communication

**✅ FULLY IMPLEMENTED**: All 15 agents support inter-agent communication.

When you mention another agent in your message using `@agent-name`, the mentioned agents
will provide their perspective on the topic.

### Example Usage

```text
@backend-developer How should we design the chat API?
@frontend-developer What UI considerations should we keep in mind?
```

This will trigger responses from both the backend and frontend developer agents,
allowing for cross-functional collaboration and diverse viewpoints.

### Communication Protocol

- Mention agents using `@agent-name` in your messages
- Agents will respond with their role-specific insights
- Multiple agents can be consulted simultaneously
- Responses include the agent's role context and relevant expertise

## Installation

1. Clone the repository
2. Run `npm install`
3. Run `npm run compile`
4. Open the extension in VS Code and press F5 to launch the Extension
Development Host
5. In the Extension Development Host, open the chat view and try invoking one
of the agents, for example: `@backend-developer What are the key responsibilities?`

## Development

- `npm run compile`: Compile TypeScript
- `npm run watch`: Watch for changes and compile
- `npm run lint`: Run ESLint

## License

See LICENSE file in the project root.
