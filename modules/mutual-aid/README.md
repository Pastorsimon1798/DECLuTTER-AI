# MutualCircle ⭕

**Community-Powered Mutual Aid Platform**

**Status:** 🚀 98% Complete | Phases 1-4 Fully Implemented | 14 Languages Supported

MutualCircle is a comprehensive mutual aid platform that combines four core features into one cohesive system:

1. **📍 Resource Locator** - Discovery: Find food pantries, shelters, healthcare, and 8+ resource types via 211 API
2. **🤝 Needs & Offers Board** - Matching: Privacy-first community needs and offers with smart matching
3. **📅 Volunteer Scheduling** - Coordination: Schedule shifts with automated SMS/email reminders
4. **👥 Pods/Micro-Circles** - Community: Sustained support through small groups with wellness check-ins and emergency broadcasts

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

## 📅 Development Status

### ✅ Completed Phases

**Phase 1: Needs & Offers Board** (100% Complete)
- Privacy-first post matching system
- Smart matching algorithm with scoring
- 10 REST API endpoints
- Full CRUD frontend with 5 pages
- Geohash-based location privacy

**Phase 2: Volunteer Scheduling** (100% Complete)
- Organization and shift management
- Automated multi-channel reminders (SMS, Email, In-app)
- 17 REST API endpoints
- Calendar views with React Big Calendar
- Capacity tracking and volunteer history

**Phase 3: Resource Locator** (100% Complete)
- 211 Open Referral API integration
- 8 resource categories (Food, Shelter, Healthcare, Legal, etc.)
- Interactive Leaflet maps with "Open Now" indicators
- Community-contributed resources with verification
- 9 REST API endpoints with intelligent caching

**Phase 4: Pods/Micro-Circles** (100% Complete)
- Close-knit support circles (2-100 members)
- Wellness check-ins with privacy controls
- Emergency SOS broadcasts
- Internal pod communication
- 21 REST API endpoints + 6 frontend pages

**Internationalization System** (100% Complete)
- 14 languages supported
- 350+ translatable strings across 6 namespaces
- Automatic language detection
- RTL support for Arabic/Hebrew
- Zero-friction contribution process

### ⏳ In Progress

**Phase 5: Polish & Launch** (30% Complete)
- Error boundaries and loading states
- Mobile responsiveness refinement
- Accessibility audit
- Performance optimization

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for comprehensive details.

## 🗃️ Database Schema

The platform uses a unified PostgreSQL database with PostGIS extension:

**Shared Tables:**
- `users` - User accounts and authentication
- `user_profiles` - Extended user information
- `notifications` - Unified notification system
- `activity_log` - Privacy-safe analytics
- `reports` - Content moderation

**Needs & Offers Tables:**
- `posts` - Needs and offers
- `matches` - Connections between users
- `contact_tokens` - Encrypted contact sharing

**Volunteer Scheduling Tables:**
- `organizations` - Volunteer organizations
- `shifts` - Volunteer shifts
- `shift_signups` - Volunteer registrations

**Pods/Micro-Circles Tables:**
- `pods` - Close-knit support circles
- `pod_members` - Member relationships with wellness tracking
- `check_ins` - Wellness check-in responses
- `sos_broadcasts` - Emergency alerts
- `pod_posts` - Internal pod communication

**Resource Locator Tables:**
- `resource_listings` - Cached 211 API data with community contributions
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

The platform is **fully internationalized** and supports **14 languages**:

### Production Ready
- 🇺🇸 **English (en)** - Complete (350+ strings)
- 🇪🇸 **Spanish (es)** - Complete

### Alpha Translations (Awaiting Native Speaker Validation)
- 🇨🇳 **Mandarin Chinese (zh-CN)** - 1.1B speakers
- 🇸🇦 **Arabic (ar)** - 274M speakers (RTL support)
- 🇮🇳 **Hindi (hi)** - 602M speakers
- 🇫🇷 **French (fr)** - 280M speakers
- 🇩🇪 **German (de)** - 134M speakers
- 🇷🇺 **Russian (ru)** - 258M speakers
- 🇯🇵 **Japanese (ja)** - 125M speakers
- 🇰🇷 **Korean (ko)** - 81M speakers
- 🇻🇳 **Vietnamese (vi)** - 85M speakers
- 🇵🇭 **Tagalog (tl)** - 82M speakers
- 🇭🇹 **Haitian Creole (ht)** - 12M speakers
- 🇧🇷 **Brazilian Portuguese (pt-BR)** - 215M speakers

**Total Reach:** 3.5+ billion speakers worldwide 🌏

Translation files: `frontend/public/locales/{language-code}/`

**Want to add your language?** See [CONTRIBUTING_TRANSLATIONS.md](CONTRIBUTING_TRANSLATIONS.md)
**Native speaker?** Help validate translations - See [TRANSLATION_VALIDATION.md](TRANSLATION_VALIDATION.md)

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

### Core Documentation
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete project overview and statistics
- **[Technical Blueprint](integrated_mutual_aid_platform.md)** - Complete technical architecture
- **[SETUP.md](SETUP.md)** - Detailed setup and installation guide
- **[USER_GUIDE.md](USER_GUIDE.md)** - End-user documentation
- **[API Documentation](http://localhost:8000/api/docs)** - Interactive API docs (when running)

### Phase Completion Guides
- [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) - Needs & Offers Board
- [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) - Volunteer Scheduling
- [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md) - Resource Locator
- [PHASE3.5_COMPLETE.md](PHASE3.5_COMPLETE.md) - Resource Type Expansion
- [PHASE4_COMPLETE.md](PHASE4_COMPLETE.md) - Pods/Micro-Circles

### Translation Documentation
- **[CONTRIBUTING_TRANSLATIONS.md](CONTRIBUTING_TRANSLATIONS.md)** - Add a new language (5 minutes!)
- **[I18N_IMPLEMENTATION.md](I18N_IMPLEMENTATION.md)** - i18n technical implementation
- **[TRANSLATION_VALIDATION.md](TRANSLATION_VALIDATION.md)** - Native speaker validation guide
- **[TRANSLATION_PRIORITIES.md](TRANSLATION_PRIORITIES.md)** - Language prioritization strategy
- **[INDIGENOUS_AFRICAN_LANGUAGES.md](INDIGENOUS_AFRICAN_LANGUAGES.md)** - Future language recommendations

### Deployment & Operations
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) - Pre-launch verification

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

## 📊 Project Statistics

**Backend:**
- 66 REST API endpoints across all features
- 22 SQLAlchemy database models
- 5 Celery background tasks
- Full authentication with JWT
- PostGIS geospatial queries

**Frontend:**
- 22+ React pages with responsive design
- Zustand state management (5 stores)
- Interactive Leaflet maps
- React Big Calendar for shift scheduling
- Full i18n support with 14 languages

**Overall Completion:** 98% (Production-ready with Phase 5 polish remaining)

## 📧 Contact & Support

- **GitHub Issues:** For bugs and feature requests
- **Discussions:** For questions and community support
- **Translations:** See [CONTRIBUTING_TRANSLATIONS.md](CONTRIBUTING_TRANSLATIONS.md)

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
