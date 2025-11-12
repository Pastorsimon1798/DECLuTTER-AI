# CommunityCircle

**Integrated Mutual Aid Platform**

CommunityCircle is a comprehensive mutual aid platform that combines four core features into one cohesive system:

1. **📍 Pantry Locator (Project 10)** - Discovery: Find food pantries and resources via 211 API
2. **🤝 Needs & Offers Board (Project 1)** - Matching: SMS-enabled community needs and offers
3. **📅 Volunteer Scheduling (Project 3)** - Coordination: Schedule shifts with automated reminders
4. **👥 Pods/Micro-Circles (Project 2)** - Community: Sustained support through small groups

## 🎯 Vision

One platform that guides users through their journey from discovering resources, to finding immediate help, to coordinating ongoing support, to building lasting community connections.

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 16 with PostGIS
- SQLAlchemy 2.0 (async)
- Celery + Redis (background jobs)
- Alembic (migrations)

**Frontend:**
- React 18 with Vite
- Tailwind CSS
- React Router v6
- Zustand (state management)
- Leaflet (maps)
- i18next (internationalization)

**Infrastructure:**
- Docker & Docker Compose
- Fly.io (production deployment)
- Plivo (SMS)
- Brevo (email)

### Project Structure

```
MutualAidApp/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tasks/          # Celery background tasks
│   │   ├── utils/          # Utilities
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # Database setup
│   │   └── main.py         # FastAPI app
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── init-db.sql         # Database initialization
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── features/      # Feature-specific components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── store/         # Zustand state stores
│   │   ├── services/      # API clients
│   │   ├── utils/         # Utilities
│   │   ├── locales/       # i18n translations
│   │   ├── styles/        # Global styles
│   │   ├── App.jsx        # Main app component
│   │   └── main.jsx       # Entry point
│   ├── public/            # Static assets
│   ├── package.json       # npm dependencies
│   ├── vite.config.js     # Vite configuration
│   └── tailwind.config.js # Tailwind configuration
│
├── docker-compose.yml      # Local development setup
├── integrated_mutual_aid_platform.md  # Technical blueprint
├── quick_start_roadmap.md  # 16-week implementation plan
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/MutualAidApp.git
cd MutualAidApp
```

### 2. Start Database & Redis

```bash
docker-compose up -d
```

This starts:
- PostgreSQL 16 with PostGIS (port 5432)
- Redis 7 (port 6379)

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
python -m app.main
```

Backend API will be available at http://localhost:8000

API Documentation: http://localhost:8000/api/docs

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at http://localhost:5173

### 5. Verify Setup

- Visit http://localhost:5173 - You should see the CommunityCircle interface
- Visit http://localhost:8000/health - Should return `{"status": "healthy"}`
- Visit http://localhost:8000/api/docs - Interactive API documentation

## 📅 Development Roadmap

This project follows a **16-week phased implementation plan**:

### Phase 1: Foundation (Weeks 1-4) ⚡
- **Goal:** Core platform + Needs & Offers Board
- **Deliverable:** Working matching system with SMS integration
- **Users:** 10 beta users actively posting

### Phase 2: Coordination (Weeks 5-8) 📅
- **Goal:** Volunteer scheduling with reminders
- **Deliverable:** Organizations can manage shifts
- **Users:** 2 organizations, 50+ users

### Phase 3: Discovery (Weeks 9-10) 📍
- **Goal:** Pantry locator via 211 API
- **Deliverable:** Search and bookmark resources
- **Users:** 100+ searches/week

### Phase 4: Community (Weeks 11-14) 👥
- **Goal:** Pods with check-ins and SOS
- **Deliverable:** Micro-circles for sustained support
- **Users:** 5 active pods

### Phase 5: Polish & Launch (Weeks 15-16) 🚀
- **Goal:** Public launch
- **Deliverable:** Integrated platform with all features
- **Users:** 50+ active users, 5+ organizations

See [quick_start_roadmap.md](quick_start_roadmap.md) for detailed week-by-week plan.

## 🗃️ Database Schema

The platform uses a unified PostgreSQL database with PostGIS extension:

**Shared Tables:**
- `users` - User accounts and authentication
- `user_profiles` - Extended user information
- `notifications` - Unified notification system
- `activity_log` - Privacy-safe analytics
- `reports` - Content moderation

**Project 1 Tables (Needs & Offers):**
- `posts` - Needs and offers
- `matches` - Connections between users
- `contact_tokens` - Encrypted contact sharing

**Project 3 Tables (Scheduling):**
- `organizations` - Volunteer organizations
- `shifts` - Volunteer shifts
- `shift_signups` - Volunteer registrations

**Project 2 Tables (Pods):**
- `pods` - Micro-circles
- `pod_memberships` - Member relationships
- `pod_posts` - Internal pod communication
- `check_in_schedules` - Automated check-ins
- `check_in_responses` - Check-in data

**Project 10 Tables (Pantry Locator):**
- `resource_listings` - Cached 211 API data
- `resource_bookmarks` - User-saved resources

See [integrated_mutual_aid_platform.md](integrated_mutual_aid_platform.md) for complete schema.

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

## 🚢 Deployment

### Production Deployment (Fly.io)

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login and create app:
```bash
fly auth login
fly launch
```

3. Set secrets:
```bash
fly secrets set SECRET_KEY=your-secret-key
fly secrets set DATABASE_URL=your-database-url
# ... other secrets
```

4. Deploy:
```bash
fly deploy
```

See deployment documentation for detailed instructions.

## 🌍 Internationalization

The platform supports multiple languages:
- **English (en)** - Default
- **Spanish (es)** - Priority for Phase 1
- Additional languages can be added via i18next

Translations are stored in `frontend/src/locales/`

## 🔐 Security & Privacy

**Privacy-First Design:**
- Geohash-based location privacy (no exact addresses stored)
- Encrypted contact information sharing
- User-controlled notification preferences
- GDPR-compliant data handling
- Regular security audits

**Authentication:**
- JWT-based authentication
- Phone verification via SMS
- Password hashing with bcrypt
- Rate limiting on sensitive endpoints

## 📚 Documentation

- [Technical Blueprint](integrated_mutual_aid_platform.md) - Complete technical architecture
- [Quick Start Roadmap](quick_start_roadmap.md) - 16-week implementation guide
- [API Documentation](http://localhost:8000/api/docs) - Interactive API docs (when running)

## 🤝 Contributing

This is an open-source mutual aid project. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style (Black for Python, Prettier for JavaScript)
- Write tests for new features
- Update documentation
- Ensure all tests pass before submitting PR
- Keep commits atomic and well-described

## 📝 License

AGPL-3.0 License - Keep it open!

This ensures the platform remains free and open-source for all communities.

## 📧 Contact & Support

- **GitHub Issues:** For bugs and feature requests
- **Discussions:** For questions and community support
- **Email:** [Your contact email]

## 🙏 Acknowledgments

Built with ❤️ for mutual aid communities everywhere.

**Inspired by:**
- Grassroots mutual aid networks
- Open-source community software
- Community resilience research

**Tech Stack Credits:**
- FastAPI, React, PostgreSQL teams
- Open-source contributors worldwide

---

**Let's build something amazing together!** 🚀

For the community, by the community.
