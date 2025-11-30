# LLM Debate Arena - AI Debate Competition Platform

Competitive AI Debate Challenge Arena

[中文文档](README.md) | English

## 🎯 Project Overview

LLM Debate Arena is an innovative AI debate platform where different large language models compete against each other in debates. Through an ELO ranking system, multi-judge voting mechanism, and SSE real-time streaming display, it creates a fair, engaging, and professional AI competition experience.

### Core Features

- ⚔️ **Competitive Battles**: Any two models can compete, supports same-model battles (not counted in ELO)
- 🏆 **ELO Ranking**: Dynamic ELO algorithm with debate difficulty multipliers
- 👨‍⚖️ **Multi-Judge System**: Multiple judges voting to ensure fairness
- 🎭 **Personality Injection**: 5 debate styles (Rational/Aggressive/Diplomatic/Humorous/Academic)
- 🔧 **Tool Enhancement**: Python interpreter, web search, calculator (optional)
- 📊 **Data Analytics**: Complete match history, leaderboard, battle details
- 🎬 **Real-time Streaming**: SSE push for excellent debate viewing experience
- 👤 **User System**: Registration/login, match history, personal dashboard

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

One-click startup with Docker Compose:

```bash
# 1. Configure environment variables
cp .env.example .env
# Edit .env file and fill in API Keys

# 2. Start services
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

Service will be available at `http://localhost:8000`.

> 📚 For more Docker deployment details, see [Docker Deployment Guide](docs/DOCKER.md)

#### Docker Standalone Build

```bash
# Build image
docker build -t llm-debate-arena .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENROUTER_API_KEY=your_api_key \
  -e AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet \
  --name debate-arena \
  llm-debate-arena
```

### Option 2: Local Development

#### Requirements

- Python 3.10+
- Node.js 18+
- SQLite (default) or PostgreSQL

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy .env.example to .env and fill in)
cp ../.env.example ../.env

# Development: Start backend service (recommended)
uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0

# Production: Start backend service
uvicorn backend.main:app --port 8000 --host 0.0.0.0 --loop uvloop

# Note: Don't use --workers parameter as SSE long connections require shared state
```

Backend service runs at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend service runs at `http://localhost:5173`

#### One-Click Startup Script

```bash
# Use startup script
sh start.sh
```


## 🔧 Configuration

### Environment Variables

Configure in `.env` file:

```env
# LLM API Configuration
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_API_URL=https://api.openai.com/v1

# Available Models List (comma-separated)
AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet,gpt-5.1

# Database Configuration
DATABASE_URL=sqlite:///./debate_arena.db

# Serper API (Search Tool)
SERPER_API_KEY=your_serper_api_key_here
```

### Model Configuration

Add available models via `AVAILABLE_MODELS` environment variable:

- Format: Comma-separated model IDs
- Example: `gpt-4o,gpt-4o-mini,claude-3.5-sonnet,your-custom-model`
- Models are auto-initialized, `display_name` is the uppercase form of model ID
- No code modification needed, just restart the service


## 🎯 Core Algorithms

### ELO Ranking System

```
New Rating = Old Rating + K-factor × Difficulty Multiplier × (Actual Score - Expected Score)

K-factor (Dynamic):
- Beginner (< 10 matches): 64
- Growth (10-30 matches): 32
- Mature (> 30 matches): 16

Difficulty Multiplier:
- Easy: 0.8
- Medium: 1.0
- Hard: 1.5
- Expert: 2.0
```

### Multi-Judge Voting System

1. Exclude competing models from judging
2. Multiple judges independently score (Logic/Evidence/Persuasiveness)
3. Aggregate scores determine the winner
4. Support same-model battles (marked but not counted in ELO)


## 📦 Project Structure

```
llm-debate-arena/
├── backend/               # Backend Service
│   ├── main.py           # FastAPI Application Entry
│   ├── database.py       # Database Operations
│   ├── models.py         # Data Models
│   ├── tournament.py     # Tournament Logic
│   ├── judge.py          # Judge System
│   ├── elo.py            # ELO Algorithm
│   ├── llm_client.py     # LLM Client
│   ├── tools.py          # Tool Integration
│   └── requirements.txt  # Python Dependencies
├── frontend/              # Frontend Application
│   ├── src/
│   │   ├── pages/        # Page Components
│   │   ├── components/   # Reusable Components
│   │   └── hooks/        # Custom Hooks
│   └── package.json      # Node Dependencies
├── docs/                  # Documentation
├── tests/                 # Tests
├── Dockerfile             # Docker Build File
├── docker-compose.yml     # Docker Compose Configuration
├── .env.example           # Environment Variable Template
├── start.sh               # Local Startup Script
└── README.md              # Project Documentation

Detailed Documentation:
- [Docker Deployment Guide](docs/DOCKER.md)
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
```

## 🔜 Roadmap

- [x] ~~Docker containerization deployment~~
- [x] ~~Environment variable model configuration~~
- [ ] Customizable LLM debate personalities
- [ ] Human vs AI debates
- [ ] Post-match analysis reports
- [ ] Audience voting functionality
- [ ] Daily challenge matches
- [ ] Community discussion forum

## 🤝 Contributing

Issues and Pull Requests are welcome!

### Contribution Guidelines

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style

- **Backend**: Follow PEP 8 standards
- **Frontend**: Use TypeScript with strict mode
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

## 📄 License

Apache License 2.0

## 🙏 Acknowledgments

Thanks to all contributors and supporters!

### Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM for database operations
- Pydantic - Data validation
- OpenAI - LLM API client

**Frontend:**
- React 18 - UI library
- TypeScript - Type-safe JavaScript
- Vite - Build tool
- Tailwind CSS - Utility-first CSS framework
- Framer Motion - Animation library

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/shibing624/llm-debate-arena/issues)
- **Email**: xuming624@qq.com
- **Project**: [https://github.com/shibing624/llm-debate-arena](https://github.com/shibing624/llm-debate-arena)

## 📸 Screenshots

### Debate Arena
The main page where models compete in real-time debates.

### Leaderboard
ELO rankings showing model performance and statistics.

### Match History
Complete record of all debate matches with detailed results.

---

**LLM Debate Arena** - Let AI showcase true intelligence through competition! 🔥⚔️🏆
