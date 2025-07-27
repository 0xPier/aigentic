# AI-Run Consultancy SaaS B2B Platform

A comprehensive multi-agent AI platform that automates business tasks through specialized AI agents with a subscription-based model.

## Architecture

- **Backend**: FastAPI with JWT authentication and subscription management
- **Frontend**: React dashboard for user interaction
- **Multi-Agent System**: CrewAI-based orchestration with 11 specialized agents
- **Database**: PostgreSQL/SQLite for user data and agent memory
- **Processing**: Async task processing with Celery
- **Deployment**: Docker containerization

## Agents

1. **Orchestrator Agent**: Task decomposition and delegation
2. **Research Agent**: Data gathering from web/APIs
3. **Analysis Agent**: Data processing and insights
4. **Recommendation Agent**: Strategic recommendations
5. **Automation Agent**: Tool integrations and CRM updates
6. **Reporting Agent**: Dashboard and report generation
7. **Social Media Agent**: X/Twitter and Telegram management
8. **Customer Care Agent**: Chatbot creation and deployment
9. **Graphics Agent**: Image and poster generation
10. **Presentation Agent**: PPT/PDF deck creation
11. **Content Agent**: Blog and long-form content creation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
cd frontend && npm install
```

2. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
# Backend
uvicorn src.api.main:app --reload

# Frontend
cd frontend && npm start

# Celery worker
celery -A src.core.celery_app worker --loglevel=info
```

## Project Structure

```
├── src/
│   ├── agents/          # AI agent implementations
│   ├── api/             # FastAPI backend
│   ├── core/            # Core utilities and config
│   ├── database/        # Database models and operations
│   └── integrations/    # Third-party API integrations
├── frontend/            # React dashboard
├── tests/               # Unit and integration tests
├── docker/              # Docker configuration
└── docs/                # Documentation
```

## Features

- Multi-agent task orchestration
- Real-time dashboard with progress tracking
- Subscription management and billing
- Secure API key management
- Async processing for long-running tasks
- Comprehensive reporting and analytics
- Social media automation
- Content generation and graphics creation
- Chatbot deployment
- Presentation and document generation

## License

MIT License
