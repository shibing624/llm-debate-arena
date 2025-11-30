[**🇨🇳中文**](https://github.com/shibing624/llm-debate-arena/blob/main/README.md) | [**🌐English**](https://github.com/shibing624/llm-debate-arena/blob/main/README_EN.md)

<div align="center">
  <a href="https://github.com/shibing624/llm-debate-arena">
    <img src="https://github.com/shibing624/llm-debate-arena/blob/main/docs/favicon.svg" height="150" alt="Logo">
  </a>
</div>

-----------------

# LLM Debate Arena - AI Debate Competition Platform
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](README.md)
[![License Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![python_version](https://img.shields.io/badge/Python-3.10%2B-green.svg)](requirements.txt)
[![GitHub issues](https://img.shields.io/github/issues/shibing624/llm-debate-arena.svg)](https://github.com/shibing624/llm-debate-arena/issues)
[![Wechat Group](https://img.shields.io/badge/wechat-group-green.svg?logo=wechat)](#Contact)


**LLM Debate Arena**: AI Debate Competition Platform - Competitive AI Debate Challenge Arena

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

### Demo Screenshots

![image.png](https://github.com/shibing624/llm-debate-arena/blob/main/docs/main.png)


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


## System Design

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Arena   │  │Leaderboard│ │ Register │  │  Login   │   │
│  │          │  │           │  │          │  │ (Modal)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │             │          │
│       └─────────────┴──────────────┴─────────────┘          │
│                     │ SSE / HTTP REST                       │
└─────────────────────┼───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                Backend API (FastAPI)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            /api/tournament/                          │  │
│  │  • POST /match/stream    (SSE Streaming Match)      │  │
│  │  • GET  /leaderboard     (Leaderboard)              │  │
│  │  • GET  /matches/history (History with filters)     │  │
│  │  • GET  /match/{id}      (Match details)            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            /api/auth/                                │  │
│  │  • POST /register        (Register)                  │  │
│  │  • POST /login           (Login with email)          │  │
│  │  • GET  /me              (Get user info)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                      ↓                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Tournament│  │  Judge   │  │   ELO    │  │   Auth   │  │
│  │ Manager  │→ │  Panel   │→ │  System  │  │   JWT    │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │              │             │          │
│       ↓             ↓              ↓             ↓          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐ │
│  │   LLM    │  │  Tools   │  │      Database            │ │
│  │  Client  │  │  Engine  │  │  (SQLAlchemy + SQLite)   │ │
│  └──────────┘  └──────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer (SQLite)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────┐│
│  │ competitors│  │  matches   │  │   topics   │  │ users ││
│  │  (models)  │  │  (matches) │  │  (topics)  │  │(users)││
│  └────────────┘  └────────────┘  └────────────┘  └───────┘│
└─────────────────────────────────────────────────────────────┘
```

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


## Contact

- Issue(Suggestions): [![GitHub issues](https://img.shields.io/github/issues/shibing624/llm-debate-arena.svg)](https://github.com/shibing624/llm-debate-arena/issues)
- Email: xuming624@qq.com
- WeChat: Add me on *WeChat ID: xuming624, note: Name-Company-NLP* to join NLP discussion group.

<img src="docs/wechat.jpeg" width="200" />


## Citation

If you use `llm-debate-arena` in your research, please cite it as follows:

APA:
```latex
Xu, M. llm-debate-arena: A debate arena for LLM(Version 1.1.2) [Computer software]. https://github.com/shibing624/llm-debate-arena
```

BibTeX:
```latex
@misc{llm-debate-arena,
  author = {Ming Xu},
  title = {llm-debate-arena: A debate arena for LLM},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/shibing624/llm-debate-arena}},
}
```

## License

The license is [The Apache License 2.0](LICENSE), free for commercial use. Please include a link to llm-debate-arena and the license in your product description.


## Contribute

The project code is still rough. If you have improvements to the code, please submit them back to this project. Before submitting, note the following:

- Add corresponding unit tests in `tests`
- Use `python -m pytest -v` to run all unit tests and ensure all tests pass

Then you can submit a PR.

## References
- [karpathy/llm_council](https://github.com/karpathy/llm-council) - The judge module was inspired by this project
