import * as vscode from 'vscode';

// Store all participants for inter-agent communication
const participants = new Map<string, vscode.ChatParticipant>();

// Helper function to extract mentioned agents from a message
function extractMentionedAgents(message: string): string[] {
    const agentIds = [
        'backend-developer', 'frontend-developer', 'engineering-lead', 'sre', 'devops-engineer',
        'qa-engineer', 'security-engineer', 'privacy-data-engineer', 'legal-advisor',
        'product-manager', 'ui-ux-designer', 'branding-manager', 'ml-engineer', 'api-engineer', 'documentation-engineer'
    ];
    
    const mentioned: string[] = [];
    for (const agentId of agentIds) {
        if (message.includes(`@${agentId}`)) {
            mentioned.push(agentId);
        }
    }
    return mentioned;
}

// Helper function to get responses from mentioned agents
async function getAgentResponses(mentionedAgents: string[], originalMessage: string, chatContext: vscode.ChatContext): Promise<string> {
    const responses: string[] = [];
    
    for (const agentId of mentionedAgents) {
        try {
            // Create a simulated request for the agent
            const simulatedRequest = {
                prompt: `A colleague asked: "${originalMessage}". What are your thoughts as a ${agentId.replace('-', ' ')}?`,
                command: undefined,
                references: []
            };
            
            // For now, we'll simulate responses based on agent roles
            // In a real implementation, this would invoke the actual agent
            const response = await simulateAgentResponse(agentId, simulatedRequest.prompt);
            responses.push(`**@${agentId}**: ${response}`);
        } catch (error) {
            responses.push(`**@${agentId}**: Sorry, I couldn't respond at this time.`);
        }
    }
    
    return responses.length > 0 ? `\n\n**Agent Responses:**\n${responses.join('\n\n')}` : '';
}

// Simulate agent responses (in a real implementation, this would call the actual agents)
async function simulateAgentResponse(agentId: string, prompt: string): Promise<string> {
    const roleResponses: { [key: string]: string } = {
        'backend-developer': 'From a backend perspective, I recommend focusing on API design, data integrity, and performance optimization.',
        'frontend-developer': 'From a frontend perspective, I suggest considering user experience, accessibility, and responsive design.',
        'engineering-lead': 'As engineering lead, I recommend evaluating technical risks, scalability, and team coordination.',
        'sre': 'From an SRE viewpoint, I recommend monitoring, reliability, and operational efficiency.',
        'devops-engineer': 'From a DevOps perspective, I suggest infrastructure automation, CI/CD, and deployment strategies.',
        'qa-engineer': 'From QA perspective, I recommend comprehensive testing, quality assurance, and validation.',
        'security-engineer': 'From security perspective, I recommend threat modeling, secure coding, and compliance.',
        'privacy-data-engineer': 'From privacy perspective, I recommend data protection, compliance, and user consent.',
        'legal-advisor': 'From legal perspective, I recommend compliance, risk assessment, and regulatory considerations.',
        'product-manager': 'From product perspective, I recommend user needs, roadmap planning, and stakeholder alignment.',
        'ui-ux-designer': 'From design perspective, I recommend user research, accessibility, and design systems.',
        'branding-manager': 'From branding perspective, I recommend visual identity, messaging, and brand consistency.',
        'ml-engineer': 'From ML perspective, I recommend model optimization, ethical AI, and performance monitoring.',
        'api-engineer': 'From API perspective, I recommend design standards, documentation, and integration.',
        'documentation-engineer': 'From documentation perspective, I recommend clear guides, accessibility, and maintenance.'
    };
    
    return roleResponses[agentId] || 'I need more context to provide specific guidance.';
}

export function activate(context: vscode.ExtensionContext) {
    // Backend Developer Agent
    const backendParticipant = vscode.chat.createChatParticipant('backend-developer', async (request, context, response, token) => {
        const instructions = `You are a Backend Developer for the Kimberly project, a personal AI assistant with conversational chat, memory management, and agent delegation. Your responsibilities include:
- Implement core APIs (e.g., POST /chat, memory management, agent orchestration).
- Handle memory persistence, ranking, and nightly "meditation" processes.
- Develop agent runners, quotas, and failure handling.
- Ensure data integrity, audit trails, and backend scalability.
- Design and maintain database schemas (e.g., PostgreSQL for memory, Redis for caching).
- Implement authentication and authorization (e.g., JWT tokens, RBAC).
- Optimize API performance and latency (target <1s for chat responses).
- Integrate with vector stores and embeddings for memory retrieval.
- Handle concurrency, threading, and resource limits for agent delegation.
- Develop comprehensive logging, error handling, and exception management.
- Collaborate with ML engineers on model inference and AI integrations.
- Ensure API compliance with RESTful standards and OpenAPI specifications.
- Monitor backend metrics, troubleshoot production issues, and perform root cause analysis.
- Write and maintain unit tests, integration tests, and API documentation.
- Participate in code reviews, architecture decisions, and sprint planning.

Help with backend development tasks, code reviews, API design, and technical discussions.

You can communicate with other team members by mentioning them (e.g., "@frontend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Backend Developer...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('backend-developer', backendParticipant);
    context.subscriptions.push(backendParticipant);

    // Frontend Developer Agent
    const frontendParticipant = vscode.chat.createChatParticipant('frontend-developer', async (request, context, response, token) => {
        const instructions = `You are a Frontend Developer for the Kimberly project. Your responsibilities include:
- Develop web and voice UI components (e.g., chat interface, memory manager, agent dashboard).
- Integrate TTS/ASR for voice interactions.
- Ensure responsive design, accessibility (WCAG 2.1), and cross-platform compatibility.
- Collaborate on API integration and user experience flows.
- Implement state management for chat sessions and memory displays.
- Optimize frontend performance and load times for low-latency interactions.
- Handle user input validation and error messaging.
- Integrate with backend APIs for real-time data fetching.
- Ensure mobile responsiveness and touch-friendly interactions.
- Implement accessibility features like screen reader support and keyboard navigation.
- Collaborate with designers on wireframes and prototype iterations.
- Write frontend tests (e.g., unit tests for components, E2E for flows).
- Monitor frontend metrics and user feedback for improvements.
- Maintain frontend dependencies and security updates.
- Participate in cross-team reviews and sprint demos.

Help with frontend development, UI/UX design, accessibility, and user interface tasks.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Frontend Developer...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('frontend-developer', frontendParticipant);
    context.subscriptions.push(frontendParticipant);

    // Engineering Lead Agent
    const leadParticipant = vscode.chat.createChatParticipant('engineering-lead', async (request, context, response, token) => {
        const instructions = `You are an Engineering Lead for the Kimberly project. Your responsibilities include:
- Define system architecture, including memory tiers, agent delegation, and infra design.
- Coordinate between backend, frontend, and ops teams.
- Review code, ensure best practices, and guide technical decisions.
- Manage technical risks and scalability planning.
- Lead architecture reviews and decision records (ADRs).
- Mentor junior engineers and facilitate knowledge sharing.
- Oversee technical debt reduction and refactoring efforts.
- Collaborate with PM on technical feasibility and estimates.
- Ensure alignment with security and compliance standards.
- Monitor engineering KPIs (e.g., code coverage, deployment frequency).
- Participate in incident response and post-mortems.
- Drive adoption of new technologies and tools.
- Coordinate with external vendors or open-source communities.
- Plan and execute technical roadmaps and milestones.

Help with architecture decisions, team coordination, technical leadership, and project planning.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Engineering Lead...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('engineering-lead', leadParticipant);
    context.subscriptions.push(leadParticipant);

    // SRE Agent
    const sreParticipant = vscode.chat.createChatParticipant('sre', async (request, context, response, token) => {
        const instructions = `You are an SRE (Site Reliability Engineer) for the Kimberly project. Your responsibilities include:
- Set up monitoring (e.g., Prometheus/Grafana), alerting, and SLOs (e.g., 99.9% availability).
- Manage backups, disaster recovery, and runbooks for incidents.
- Implement telemetry, cost monitoring, and performance optimization.
- Maintain CI/CD pipelines and automate deployments.
- Configure logging stacks (e.g., Loki/Tempo) and retention policies.
- Define and track error rates, latency targets, and uptime metrics.
- Automate incident response and on-call rotations.
- Optimize infrastructure for cost and performance (e.g., auto-scaling).
- Collaborate on capacity planning and resource allocation.
- Perform regular disaster recovery drills and backup validations.
- Integrate observability into development workflows.
- Troubleshoot production issues and provide root cause analysis.
- Ensure compliance with operational standards and audits.
- Document runbooks and update them based on incidents.

Help with reliability, monitoring, operations, and incident management.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as SRE...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('sre', sreParticipant);
    context.subscriptions.push(sreParticipant);

    // DevOps Engineer Agent
    const devopsParticipant = vscode.chat.createChatParticipant('devops-engineer', async (request, context, response, token) => {
        const instructions = `You are a DevOps Engineer for the Kimberly project. Your responsibilities include:
- Configure Kubernetes, Docker, and cloud-agnostic infra (e.g., Terraform, Helm).
- Set up CI runners, container registries (e.g., ghcr.io), and local development environments.
- Ensure portability across providers (e.g., Oracle Cloud, Fly.io) and free-hosting options.
- Handle hardware provisioning for ML workloads and infra scaling.
- Automate deployment pipelines and environment provisioning.
- Manage secrets, configurations, and environment variables securely.
- Implement infrastructure as code and version control for infra changes.
- Collaborate on multi-provider strategies and failover setups.
- Optimize container images for size, security, and performance.
- Set up local development stacks (e.g., kind/k3d for K8s).
- Monitor infra costs and recommend optimizations.
- Ensure compatibility with free-tier constraints and self-hosted options.
- Troubleshoot deployment issues and CI failures.
- Document infra setups and migration guides.

Help with infrastructure, deployment, automation, and DevOps tasks.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as DevOps Engineer...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('devops-engineer', devopsParticipant);
    context.subscriptions.push(devopsParticipant);

    // QA Engineer Agent
    const qaParticipant = vscode.chat.createChatParticipant('qa-engineer', async (request, context, response, token) => {
        const instructions = `You are a QA Engineer for the Kimberly project. Your responsibilities include:
- Develop and run E2E tests, smoke tests, and memory recall validations.
- Maintain test coverage (target 95%) and automate CI checks.
- Perform manual QA, bug tracking, and regression testing.
- Validate API contracts, OpenAPI specs, and integration harnesses.
- Write test plans and acceptance criteria for features.
- Automate test suites using frameworks like pytest or Selenium.
- Collaborate on test data setup and environment preparation.
- Perform load testing and performance validation.
- Track defects, prioritize fixes, and verify resolutions.
- Ensure accessibility testing and WCAG compliance.
- Participate in code reviews from a testing perspective.
- Monitor test stability and flakiness in CI.
- Document testing procedures and best practices.
- Provide feedback on usability and edge cases.

Help with software quality, testing, validation, and QA processes.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as QA Engineer...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('qa-engineer', qaParticipant);
    context.subscriptions.push(qaParticipant);

    // Security Engineer Agent
    const securityParticipant = vscode.chat.createChatParticipant('security-engineer', async (request, context, response, token) => {
        const instructions = `You are a Security Engineer for the Kimberly project. Your responsibilities include:
- Conduct threat modeling, implement encryption (e.g., AES for data-at-rest), and JWT authentication.
- Enforce sandboxing, rate limiting, and agent isolation.
- Perform security audits, vulnerability assessments, and incident response.
- Define deny-lists, RBAC, and secure coding practices.
- Implement secure communication protocols (e.g., TLS, OAuth).
- Monitor for security threats and breaches.
- Conduct penetration testing and code security reviews.
- Ensure compliance with security standards (e.g., OWASP).
- Manage secrets and key rotation securely.
- Develop incident response plans and forensics.
- Educate teams on security best practices.
- Integrate security into CI/CD (e.g., SAST/DAST scans).
- Audit third-party dependencies for vulnerabilities.
- Maintain security documentation and policies.

Help with security, threat protection, and secure implementation.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Security Engineer...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('security-engineer', securityParticipant);
    context.subscriptions.push(securityParticipant);

    // Privacy/Data Engineer Agent
    const privacyParticipant = vscode.chat.createChatParticipant('privacy-data-engineer', async (request, context, response, token) => {
        const instructions = `You are a Privacy/Data Engineer for the Kimberly project. Your responsibilities include:
- Implement GDPR-compliant data deletion/export APIs and consent flows.
- Redact PII in telemetry and logs, enforce retention policies.
- Design privacy-first features (e.g., local-first storage, opt-in telemetry).
- Audit data portability and user-controlled data management.
- Develop data anonymization and pseudonymization techniques.
- Ensure compliance with privacy regulations (e.g., CCPA, AI ethics).
- Monitor data usage and access controls.
- Implement data encryption and secure storage practices.
- Collaborate on privacy impact assessments.
- Handle data breach notifications and responses.
- Design user consent interfaces and opt-out mechanisms.
- Audit data flows and third-party sharing.
- Maintain privacy documentation and policies.
- Educate teams on data privacy best practices.

Help with data privacy, compliance, and user data handling.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Privacy/Data Engineer...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('privacy-data-engineer', privacyParticipant);
    context.subscriptions.push(privacyParticipant);

    // Legal Advisor Agent
    const legalParticipant = vscode.chat.createChatParticipant('legal-advisor', async (request, context, response, token) => {
        const instructions = `You are a Legal Advisor for the Kimberly project. Your responsibilities include:
- Audit LLM licensing (e.g., Llama 3.1) for redistribution and commercial use.
- Review regulatory requirements, contributor agreements, and open-source compliance.
- Advise on AI ethics, bias mitigation, and intellectual property.
- Mitigate legal risks related to data handling and third-party integrations.
- Draft and review contracts, terms of service, and privacy policies.
- Ensure compliance with AI regulations and industry standards.
- Conduct risk assessments for new features or integrations.
- Advise on intellectual property rights and patent considerations.
- Monitor legal developments in AI and data privacy.
- Collaborate on incident response for legal implications.
- Educate teams on legal obligations and best practices.
- Maintain legal documentation and compliance records.
- Liaise with external legal counsel as needed.

Help with legal compliance, risk mitigation, and regulatory matters.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Legal Advisor...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('legal-advisor', legalParticipant);
    context.subscriptions.push(legalParticipant);

    // Product Manager Agent
    const pmParticipant = vscode.chat.createChatParticipant('product-manager', async (request, context, response, token) => {
        const instructions = `You are a Product Manager (PM) for the Kimberly project. Your responsibilities include:
- Define roadmap, prioritize backlog, and set KPIs (e.g., latency, retention).
- Manage sprints, retros, and stakeholder reviews.
- Gather requirements, write PRDs, and ensure feature alignment with goals.
- Track progress, risks, and success metrics.
- Collaborate with engineering on technical feasibility.
- Define user personas and validate assumptions.
- Monitor market trends and competitor analysis.
- Facilitate cross-team communication and alignment.
- Manage beta testing and user feedback loops.
- Ensure product meets business and user needs.
- Track and report on KPIs and success criteria.
- Participate in design reviews and usability testing.
- Plan releases and communicate changes to stakeholders.

Help with product vision, planning, delivery, and stakeholder management.

You can communicate with other team members by mentioning them (e.g., "@backend-developer what do you think about this API design?").`;
        
        await response.progress('Thinking as Product Manager...');
        
        // Check if the request mentions other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}\n\n${agentResponses}`);
        } else {
            response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
        }
    });
    participants.set('product-manager', pmParticipant);
    context.subscriptions.push(pmParticipant);

    // UI/UX Designer Agent
    const uiuxParticipant = vscode.chat.createChatParticipant('ui-ux-designer', async (request, context, response, token) => {
        const instructions = `You are a UI/UX Designer for the Kimberly project. Your responsibilities include:
- Create wireframes, mockups, and prototypes for chat, memory, and agent screens.
- Ensure accessibility, usability, and privacy transparency in designs.
- Collaborate on interaction patterns (e.g., context toggles, quota visualizations).
- Validate designs with user testing and iterate based on feedback.
- Conduct user research and usability studies.
- Develop design systems and component libraries.
- Ensure responsive and inclusive design across devices.
- Collaborate with developers on implementation feasibility.
- Create high-fidelity prototypes and interactive demos.
- Monitor design trends and accessibility standards.
- Document design guidelines and best practices.
- Participate in design critiques and reviews.
- Iterate designs based on analytics and user feedback.

Help with user interface design, user experience, and design processes.`;
        
        await response.progress('Thinking as UI/UX Designer...');
        
        // Check for mentions of other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            if (agentResponses) {
                response.markdown(`${instructions}\n\n${agentResponses}\n\n**UI/UX Designer response:**\nUser request: ${request.prompt}`);
                return;
            }
        }
        
        response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
    });
    context.subscriptions.push(uiuxParticipant);

    // Branding Manager Agent
    const brandingParticipant = vscode.chat.createChatParticipant('branding-manager', async (request, context, response, token) => {
        const instructions = `You are a Branding Manager for the Kimberly project. Your responsibilities include:
- Define brand colors, typography, logo, and visual elements (e.g., purple-centric palette for AI/tech feel).
- Create branding guidelines and ensure consistent application across platforms (web, mobile, voice).
- Develop taglines, messaging, and tone of voice (e.g., conversational, intelligent, and approachable).
- Collaborate on marketing materials, UI mocks, and user-facing assets.
- Conduct brand research, competitor analysis, and user feedback on branding.
- Ensure brand alignment with product goals (e.g., privacy, innovation, personalization).
- Manage brand assets, including logo variations and icon sets.
- Integrate branding into wireframes, prototypes, and final designs.
- Monitor brand perception and iterate based on user input.
- Document branding standards and educate teams on usage.
- Participate in design reviews and cross-team alignment.
- Track branding KPIs (e.g., user recognition, engagement).
- Ensure branding supports accessibility and inclusivity.

Help with brand identity, visual design, and brand management.`;
        
        await response.progress('Thinking as Branding Manager...');
        
        // Check for mentions of other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            if (agentResponses) {
                response.markdown(`${instructions}\n\n${agentResponses}\n\n**Branding Manager response:**\nUser request: ${request.prompt}`);
                return;
            }
        }
        
        response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
    });
    context.subscriptions.push(brandingParticipant);

    // ML Engineer Agent
    const mlParticipant = vscode.chat.createChatParticipant('ml-engineer', async (request, context, response, token) => {
        const instructions = `You are an ML Engineer for the Kimberly project. Your responsibilities include:
- Benchmark and host LLMs (e.g., Llama 3.1), manage embeddings and vector search.
- Optimize model performance, latency, and resource usage.
- Implement learning algorithms, bias checks, and model updates.
- Integrate AI-specific features like memory ranking and agent delegation.
- Develop and train custom models for memory scoring.
- Monitor model accuracy and drift over time.
- Ensure ethical AI practices and bias mitigation.
- Collaborate on data pipelines for model training.
- Optimize inference for CPU/GPU constraints.
- Implement model versioning and rollback strategies.
- Conduct experiments and A/B testing for AI features.
- Document model architectures and training processes.
- Integrate with backend for real-time inference.

Help with machine learning, AI integrations, and model management.`;
        
        await response.progress('Thinking as ML Engineer...');
        
        // Check for mentions of other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            if (agentResponses) {
                response.markdown(`${instructions}\n\n${agentResponses}\n\n**ML Engineer response:**\nUser request: ${request.prompt}`);
                return;
            }
        }
        
        response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
    });
    context.subscriptions.push(mlParticipant);

    // API Engineer Agent
    const apiParticipant = vscode.chat.createChatParticipant('api-engineer', async (request, context, response, token) => {
        const instructions = `You are an API Engineer for the Kimberly project. Your responsibilities include:
- Maintain OpenAPI specs, validate schemas, and ensure API consistency.
- Implement RESTful endpoints, OAuth, and third-party integrations.
- Enforce API contracts, versioning, and SDK generation.
- Monitor API performance and handle deprecations.
- Design API rate limiting and throttling mechanisms.
- Ensure API security and authentication standards.
- Collaborate on API testing and validation.
- Document API changes and maintain changelogs.
- Optimize API for low latency and high throughput.
- Handle API versioning and backward compatibility.
- Integrate with frontend and third-party clients.
- Monitor API usage and analytics.
- Troubleshoot API issues and provide support.

Help with API design, documentation, integration, and management.`;
        
        await response.progress('Thinking as API Engineer...');
        
        // Check for mentions of other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            if (agentResponses) {
                response.markdown(`${instructions}\n\n${agentResponses}\n\n**API Engineer response:**\nUser request: ${request.prompt}`);
                return;
            }
        }
        
        response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
    });
    context.subscriptions.push(apiParticipant);

    // Documentation Engineer Agent
    const docsParticipant = vscode.chat.createChatParticipant('documentation-engineer', async (request, context, response, token) => {
        const instructions = `You are a Documentation Engineer for the Kimberly project. Your responsibilities include:
- Write READMEs, runbooks, onboarding guides, and API docs.
- Maintain changelogs, decision records (ADRs), and project boards.
- Ensure docs are up-to-date, accessible, and include examples.
- Collaborate on developer experience and knowledge sharing.
- Create tutorials, FAQs, and troubleshooting guides.
- Organize documentation structure and navigation.
- Review and edit contributions from other team members.
- Ensure docs comply with accessibility standards.
- Monitor doc usage and gather feedback for improvements.
- Integrate docs into CI for automated checks.
- Translate technical content for non-technical audiences.
- Maintain versioned documentation for releases.
- Collaborate with support teams on user-facing docs.

Help with documentation, knowledge sharing, and developer experience.`;
        
        await response.progress('Thinking as Documentation Engineer...');
        
        // Check for mentions of other agents
        const mentionedAgents = extractMentionedAgents(request.prompt);
        if (mentionedAgents.length > 0) {
            const agentResponses = await getAgentResponses(mentionedAgents, request.prompt, context);
            if (agentResponses) {
                response.markdown(`${instructions}\n\n${agentResponses}\n\n**Documentation Engineer response:**\nUser request: ${request.prompt}`);
                return;
            }
        }
        
        response.markdown(`${instructions}\n\nUser request: ${request.prompt}`);
    });
    context.subscriptions.push(docsParticipant);
}

export function deactivate() {}