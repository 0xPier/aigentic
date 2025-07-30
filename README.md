# AI Agent Platform

A comprehensive multi-agent AI platform built with FastAPI, Next.js, and MongoDB. This platform enables you to create, manage, and orchestrate AI agents for various tasks including research, content creation, data analysis, and automation.

## 🚀 Features

### Core Platform
- **Multi-Agent System**: 11 specialized AI agents for different tasks
- **Task Management**: Create, assign, and track AI-powered tasks
- **Project Organization**: Group tasks into projects for better organization
- **Real-time Dashboard**: Monitor agent performance and system status
- **API-First Design**: RESTful API for easy integration
- **Modern UI**: React-based frontend with Material-UI components

### AI Agents
- **Research Agent**: Web scraping, market research, trend analysis
- **Analysis Agent**: Data processing, statistical analysis, insights generation
- **Content Agent**: Blog writing, article creation, SEO optimization
- **Social Media Agent**: Twitter/Telegram management, engagement tracking
- **Graphics Agent**: Image generation, poster creation, visual content
- **Presentation Agent**: PowerPoint creation, slide design, PDF generation
- **Automation Agent**: CRM integration, workflow automation, API calls
- **Reporting Agent**: Dashboard creation, KPI tracking, analytics reporting
- **Customer Care Agent**: Chatbot creation, support automation
- **Recommendation Agent**: Strategic planning, decision support
- **Orchestrator Agent**: Task coordination and delegation

### Technical Features
- **Docker Support**: Complete containerization for easy deployment
- **MongoDB Database**: Scalable NoSQL database for data storage
- **Redis Caching**: High-performance caching layer
- **Celery Tasks**: Asynchronous task processing
- **CORS Support**: Cross-origin resource sharing enabled
- **Health Checks**: System monitoring and status endpoints

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **MongoDB**: NoSQL database
- **Redis**: Caching and message broker
- **Celery**: Asynchronous task queue
- **Motor**: Async MongoDB driver

### Frontend
- **Next.js**: React framework
- **Material-UI**: React component library
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and load balancer

## 📋 Prerequisites

- Docker and Docker Compose
- Git
- At least 4GB RAM available for containers

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/0xPier/aigentic.git
cd aigentic
```

### 2. Configure Environment
Copy the example environment file and configure your settings:
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```env
# Application Settings
ENVIRONMENT=development
DEBUG=True

# Database Configuration
DATABASE_URL=mongodb://mongo:27017/agentic_platform

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_URL=http://localhost:8000/api

# Frontend Configuration
FRONTEND_URL=http://localhost:3000

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
```

### 3. Start the Application
```bash
docker-compose up --build -d
```

### 4. Access the Platform
- **Main Application**: http://localhost:8080
- **Frontend Direct**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📚 API Documentation

The API is fully documented with OpenAPI/Swagger. Access the interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
- `GET /health` - Health check
- `GET /api/agents/` - List all agents
- `GET /api/agents/performance` - Agent performance metrics
- `GET /api/dashboard/` - Dashboard data
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create new task

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx Proxy   │    │   Backend API   │
│   (Next.js)     │◄──►│   (Port 8080)   │◄──►│   (FastAPI)     │
│   (Port 3000)   │    │                 │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   MongoDB       │    │   Redis         │
                       │   (Port 27017)  │    │   (Port 6379)   │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                              ┌─────────────────┐
                                              │   Celery        │
                                              │   Workers       │
                                              └─────────────────┘
```

## 🔧 Development

### Running in Development Mode
```bash
# Start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Testing the Application
```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/agents/

# Test frontend
curl http://localhost:3000
```

### Database Management
```bash
# Access MongoDB shell
docker exec -it agentic_mongo mongosh

# Backup database
docker exec agentic_mongo mongodump --out /backup

# Restore database
docker exec agentic_mongo mongorestore /backup
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8080
   # Kill the process or change ports in docker-compose.yml
   ```

2. **MongoDB Connection Issues**
   ```bash
   # Check MongoDB logs
   docker-compose logs mongo
   # Ensure DATABASE_URL is correct in .env
   ```

3. **Frontend Not Loading**
   ```bash
   # Check frontend logs
   docker-compose logs nextjs_frontend
   # Rebuild frontend
   docker-compose up --build -d nextjs_frontend
   ```

4. **CORS Issues**
   - Ensure nginx configuration is correct
   - Check that frontend is accessing the correct API URL
   - Verify CORS settings in backend configuration

### Health Checks
```bash
# Check all container status
docker-compose ps

# Check specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs nginx
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/0xPier/aigentic/issues) page
2. Create a new issue with detailed information
3. Include logs and error messages

## 🎯 Roadmap

- [ ] Add more AI agents (translation, code generation, etc.)
- [ ] Implement agent learning and improvement
- [ ] Add user authentication and authorization
- [ ] Create agent marketplace
- [ ] Add real-time notifications
- [ ] Implement advanced analytics and reporting
- [ ] Add mobile application
- [ ] Create deployment guides for cloud platforms

---

**Built with ❤️ using modern web technologies**
