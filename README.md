<div align="center">

# 🤖 Human-in-the-Loop (HITL) Service

### *Intelligent Human Oversight for AI Chat Systems*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*A production-ready FastAPI microservice that adds intelligent human approval workflows to AI conversations, ensuring safety, efficiency, and cost-effectiveness.*

[Features](#-features) • [Quick Start](#-quick-start) • [API Docs](#-api-endpoints) • [Architecture](#-architecture) • [Demo](#-demo)

</div>

---

## ✨ Features

### 🔐 **Sensitive Data Detection**
Automatically detects and flags sensitive information in real-time:
- 📧 Email addresses
- 📱 Phone numbers
- 🆔 Social Security Numbers (SSN)
- 💳 Credit card numbers
- 🔑 API keys and passwords

**User Action:** Mask data or block message before processing

---

### 🚀 **Intelligent Model Switching**
Analyzes query complexity and recommends optimal AI models:
- 📊 Complexity scoring based on length, technical keywords, and code indicators
- 💰 Cost vs. quality tradeoff recommendations
- 🎯 Automatic model suggestions (Gemini Flash → Gemini Pro)

**User Action:** Accept advanced model or continue with current

---

### 💬 **Smart Chat Compression**
Maintains conversation performance at scale:
- ⏱️ Triggers at conversation milestones (10th & 20th message)
- 🗜️ Compresses chat history to maintain response speed
- 📝 Preserves context while optimizing token usage

**User Action:** Approve compression to keep responses fast

---

### 📊 **Real-Time Admin Dashboard**
Monitor all HITL events with live analytics:
- 📈 Stats: Total, Shown, Accepted, Rejected, Expired
- 🔍 Advanced filtering (Conversation ID, Feature, Status)
- ⏰ Auto-refresh every 10 seconds
- 📋 Complete audit trail

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Chat UI       │
│  (Frontend)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  HITL Service   │─────▶│      KEY        │
│  (FastAPI)      │      │  (Gemini Models) │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│  (Event Store)  │
└─────────────────┘
```

**Key Components:**
- **FastAPI Backend**: Async REST API with background task processing
- **PostgreSQL**: Event storage with JSONB metadata
- **google Api**: Google Gemini models for chat responses
- **Modern UI**: Glassmorphism design with typing animations

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Google Cloud account (for google api)

### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/hitl-service.git
cd hitl-service
```

### 2️⃣ Configure Environment
```bash
cp .env.example .env.local
# Edit .env.local with your credentials
```



### 3️⃣ Add Google Cloud Credentials
Place your `google-credentials.json` file in the project root.

### 4️⃣ Start Services
```bash
docker-compose up -d
```

### 5️⃣ Access Applications
- **Chat Interface**: http://localhost:8003/
- **Admin Dashboard**: http://localhost:8003/dashboard
- **API Documentation**: http://localhost:8003/docs
- **Health Check**: http://localhost:8003/health

---

## 📡 API Endpoints

### Chat
```http
POST /hitl/api/v1/chat
```
Send message and get AI response with automatic HITL checks.

### Sensitive Data Detection
```http
POST /hitl/api/v1/hitl/features/sensitive_data/check
```
Check message for sensitive information.

### Model Switch Recommendation
```http
POST /hitl/api/v1/hitl/features/model_switch/check
```
Analyze query complexity and get model recommendation.

### Chat Compression
```http
GET /hitl/api/v1/hitl/features/chat_compression/check
```
Check if compression should be triggered.

### Submit User Response
```http
POST /hitl/api/v1/hitl/events/respond
```
Submit user's decision (accepted/rejected).

### List Events
```http
GET /hitl/api/v1/hitl/events
```
Retrieve HITL events with filtering.

**Full API Documentation**: http://localhost:8003/docs

---

## 🗂️ Project Structure

```
hitl-service/
├── src/
│   ├── config/              # Environment configuration
│   ├── db/
│   │   ├── migrations/      # SQL schema migrations
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   └── session.py       # Database connection
│   ├── models/
│   │   └── schemas.py       # Pydantic request/response schemas
│   ├── routes/
│   │   ├── chat.py          # Chat endpoint with HITL integration
│   │   └── reviews.py       # HITL feature endpoints
│   ├── services/
│   │   ├── complexity_analyzer.py   # Query complexity scoring
│   │   ├── sensitive_detector.py    # PII detection
│   │   └── review_store.py          # Database CRUD operations
│   ├── static/
│   │   ├── chat.html        # Modern chat interface
│   │   └── dashboard.html   # Admin monitoring dashboard
│   ├── deps.py              # FastAPI dependencies
│   └── main.py              # Application entry point
├── docker-compose.yml       # Docker services configuration
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
└── .env.example             # Environment template
```

---

## 🛠️ Technology Stack

| Category | Technology |
|----------|-----------|
| **Backend** | FastAPI, Python 3.11, SQLAlchemy (async) |
| **Database** | PostgreSQL 15 with JSONB |
| **AI/ML** | Google api key (Gemini 2.0 Flash, Gemini 1.5 Pro) |
| **Frontend** | Vanilla JavaScript, HTML5, CSS3 |
| **DevOps** | Docker, Docker Compose |
| **Logging** | Structlog |
| **Validation** | Pydantic v2 |

---

## 🎨 Demo

### Chat Interface
Modern glassmorphism design with:
- ✨ Animated gradient background
- 💬 Typing animation (ChatGPT-style)
- 🎭 Floating particles effect
- 📱 Fully responsive

### Admin Dashboard
Real-time monitoring with:
- 📊 Live statistics cards
- 🔍 Advanced filtering
- 📋 Event history table
- ⏰ Auto-refresh

---

## 🔧 Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally (without Docker)
```bash
python src/main.py
```

### Database Migrations
Migrations run automatically on startup. Manual execution:
```bash
# Migrations are in src/db/migrations/local/
```

### Adding New HITL Features

1. **Add feature to database**:
```sql
INSERT INTO hitl.hitl_feature_registry (feature_key, enabled)
VALUES ('your_feature', true);
```

2. **Create detection logic** in `src/services/`

3. **Add endpoint** in `src/routes/reviews.py`

4. **Integrate** in `src/routes/chat.py`

---

## 📊 Database Schema

### `hitl_feature_registry`
Stores feature configuration and enable/disable flags.

| Column | Type | Description |
|--------|------|-------------|
| feature_key | VARCHAR | Unique feature identifier |
| enabled | BOOLEAN | Feature toggle |
| created_at | TIMESTAMP | Creation time |

### `hitl_events`
Tracks every HITL popup shown and user response.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Event ID |
| conversation_id | VARCHAR | Chat conversation ID |
| feature_key | VARCHAR | Feature that triggered |
| pair_count | INTEGER | Message count |
| status | VARCHAR | shown/accepted/rejected/expired |
| user_response | VARCHAR | User's decision |
| event_metadata | JSONB | Additional context |
| created_at | TIMESTAMP | Event creation time |
| responded_at | TIMESTAMP | User response time |

---

## 🔒 Security Features

- 🔐 JWT authentication support (configurable)
- 🛡️ CORS middleware for cross-origin requests
- 🔍 PII detection and masking
- 📝 Complete audit trail
- ⏱️ SLA-based event expiry (default: 300s)

---

## 🚢 Deployment

### Docker Production Build
```bash
docker build -t hitl-service:latest .
docker run -p 8003:8003 --env-file .env hitl-service:latest
```

### Environment Variables
See `.env.example` for all configuration options.

### Health Monitoring
```bash
curl http://localhost:8003/health
```

Response:
```json
{
  "status": "ok",
  "service": "hitl-service",
  "version": "1.0.0",
  "env": "local"
}
```

---

## 🧪 Testing

### Test Sensitive Data Detection
```bash
curl -X POST http://localhost:8003/hitl/api/v1/hitl/features/sensitive_data/check \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test", "message": "My email is test@example.com"}'
```

### Test Model Switch
```bash
curl -X POST http://localhost:8003/hitl/api/v1/hitl/features/model_switch/check \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "test", "query": "Explain quantum computing with code", "current_model": "gemini-2.0-flash-lite"}'
```

---

## 📈 Performance

- ⚡ Async database operations
- 🔄 Background task for event expiry
- 💾 In-memory conversation caching
- 🚀 Optimized for high throughput

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/shivam)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)

---

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Google Cloud for google api
- PostgreSQL for reliable data storage
- The open-source community

---

<div align="center">

### ⭐ Star this repo if you find it helpful!

Made with ❤️ and ☕

</div>
