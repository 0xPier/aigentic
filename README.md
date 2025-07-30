# AI Agent Platform (aigentic)

A full-stack AI Agent Platform built with Next.js, FastAPI, and MongoDB. This platform provides a comprehensive solution for managing AI agents, tasks, and projects with a modern web interface and robust backend infrastructure.

## 🚀 Features

### Frontend (Next.js)
- **Modern UI** with Material-UI components
- **Responsive Design** that works on all devices
- **Navigation System** with sidebar and routing
- **Dashboard** with real-time statistics
- **Task Management** interface
- **Agent Management** system
- **Project Organization** tools
- **Settings & Configuration** panels
- **Integration Management** for external services

### Backend (FastAPI)
- **RESTful API** with automatic documentation
- **MongoDB Integration** with async operations
- **User Authentication** and authorization
- **Task Processing** with Celery and Redis
- **Real-time Updates** for dashboard statistics
- **Modular Architecture** with clean separation of concerns
- **Docker Support** for easy deployment

### Infrastructure
- **Docker Compose** for multi-service orchestration
- **Nginx Proxy** for routing and load balancing
- **Redis** for caching and task queuing
- **MongoDB** for data persistence
- **Environment-based Configuration**

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** - React framework with SSR support
- **Material-UI (MUI) v5** - Modern React UI library
- **Emotion** - CSS-in-JS styling
- **Axios** - HTTP client for API calls
- **React Query** - Data fetching and caching

### Backend
- **FastAPI** - Modern Python web framework
- **PyMongo** - MongoDB driver with async support
- **Pydantic** - Data validation and settings management
- **Celery** - Distributed task queue
- **Redis** - In-memory data structure store
- **CrewAI** - AI agent orchestration

### Database & Infrastructure
- **MongoDB** - NoSQL database
- **Redis** - Cache and message broker
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy and load balancer

## 📋 Prerequisites

- **Docker** and **Docker Compose**
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **Git**

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/aigentic.git
cd aigentic
```

### 2. Environment Setup
```bash
# Copy environment files
cp .env.example .env
cp nextjs-frontend/.env.local.example nextjs-frontend/.env.local

# Update environment variables as needed
```

### 3. Start with Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080/api
- **API Documentation**: http://localhost:8080/docs

## 🔧 Development Setup

### Frontend Development
```bash
cd nextjs-frontend
npm install
npm run dev
```

### Backend Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Setup
```bash
# Start MongoDB and Redis
docker-compose up mongo redis -d
```

## 📁 Project Structure

```
aigentic/
├── nextjs-frontend/          # Next.js frontend application
│   ├── components/           # Reusable UI components
│   ├── pages/               # Next.js pages and routing
│   ├── src/                 # Utilities and configurations
│   └── styles/              # Global styles
├── src/                     # FastAPI backend application
│   ├── api/                 # API routes and endpoints
│   ├── core/                # Core configurations
│   ├── database/            # Database models and connections
│   ├── agents/              # AI agent implementations
│   └── services/            # Business logic services
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Multi-service orchestration
└── requirements.txt         # Python dependencies
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /api/dashboard/` - Dashboard statistics
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create new task
- `GET /api/agents/` - List agents
- `POST /api/agents/` - Create new agent
- `GET /api/projects/` - List projects
- `POST /api/projects/` - Create new project

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh token

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nextjs_frontend | 3000 | Next.js frontend application |
| backend | 8000 | FastAPI backend API |
| nginx | 8080 | Reverse proxy and load balancer |
| mongo | 27017 | MongoDB database |
| redis | 6379 | Redis cache and message broker |
| celery_worker | - | Background task processor |
| celery_beat | - | Scheduled task manager |

## 🔒 Environment Variables

### Backend (.env)
```bash
ENVIRONMENT=development
DATABASE_URL=mongodb://mongo:27017/agentic_platform
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## 🧪 Testing

### Run Backend Tests
```bash
pytest tests/
```

### Run Frontend Tests
```bash
cd nextjs-frontend
npm test
```

## 🚀 Deployment

### Production Deployment
1. Update environment variables for production
2. Build and deploy with Docker Compose:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-specific Configurations
- Development: Local setup with hot reload
- Staging: Docker setup with staging data
- Production: Optimized builds with production database

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint for API documentation
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions and ideas

## 🎯 Roadmap

- [ ] Advanced AI agent capabilities
- [ ] Real-time collaboration features
- [ ] Mobile application
- [ ] Advanced analytics and reporting
- [ ] Integration with more AI services
- [ ] Multi-tenancy support
- [ ] Advanced security features

## 📊 Features in Detail

### Dashboard
- Real-time task statistics
- Agent performance metrics
- Project progress tracking
- System health monitoring

### Task Management
- Create and assign tasks to agents
- Monitor task execution
- View task history and logs
- Task scheduling and automation

### Agent Management
- Deploy and configure AI agents
- Monitor agent performance
- Agent capability management
- Custom agent creation

### Project Organization
- Create and manage projects
- Team collaboration tools
- Resource allocation
- Progress tracking

---

Built with ❤️ by the AI Agent Platform Team
