# CommunityCircle - Setup & Running Guide

## Quick Start (Development)

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose**
- **Git**

### 1. Start Infrastructure

```bash
# Start PostgreSQL + PostGIS and Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file (already created)
# Edit backend/.env if needed for your setup

# Run database migrations
alembic upgrade head

# Start backend server
python -m app.main
```

Backend will be available at:
- **API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/api/docs
- **API Docs (ReDoc):** http://localhost:8000/api/redoc

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## Testing the Application

### 1. Create a User Account

1. Navigate to http://localhost:5173/register
2. Fill in the registration form:
   - **Pseudonym:** Your display name (e.g., "helper123")
   - **Email or Phone:** Provide at least one
   - **Password:** Min 8 chars, must include uppercase, lowercase, and digit
3. Click "Create account"
4. You'll be automatically logged in and redirected to the dashboard

### 2. Test Authentication

1. Log out from the dashboard
2. Navigate to http://localhost:5173/login
3. Login with your credentials:
   - **Username:** Can be your email, phone, or pseudonym
   - **Password:** Your password

### 3. Test API Directly

You can test the API using the Swagger UI:

1. Navigate to http://localhost:8000/api/docs
2. Try the endpoints:
   - **POST /api/auth/register** - Register a user
   - **POST /api/auth/login** - Login
   - **GET /api/auth/me** - Get current user (requires authentication)
   - **POST /api/posts** - Create a post (requires authentication)
   - **GET /api/posts** - Search posts

### 4. Create Test Data

Use the API docs or create a test script:

```python
import requests

# API base URL
API_URL = "http://localhost:8000/api"

# Login
response = requests.post(
    f"{API_URL}/auth/login",
    data={"username": "helper123", "password": "YourPassword123"}
)
token = response.json()["access_token"]

# Create a need post
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{API_URL}/posts",
    json={
        "type": "NEED",
        "category": "food",
        "title": "Need groceries this week",
        "description": "Looking for help with grocery shopping",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "radius_meters": 2000,
        "visibility": "public"
    },
    headers=headers
)
print(response.json())
```

## Database Management

### View Database

```bash
# Connect to PostgreSQL
docker exec -it communitycircle-db psql -U postgres -d communitycircle

# List tables
\dt

# View users
SELECT pseudonym, email, created_at FROM users;

# View posts
SELECT type, title, status, created_at FROM posts;

# Exit
\q
```

### Reset Database

```bash
cd backend

# Downgrade all migrations
alembic downgrade base

# Run migrations again
alembic upgrade head
```

### Create New Migration

```bash
cd backend

# After modifying models in app/models/
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration in alembic/versions/

# Apply the migration
alembic upgrade head
```

## Troubleshooting

### Backend Issues

**Issue: ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Issue: Database connection error**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart db

# Check logs
docker-compose logs db
```

**Issue: Migration errors**
```bash
# Check current migration state
alembic current

# View migration history
alembic history

# Downgrade and re-apply
alembic downgrade -1
alembic upgrade head
```

### Frontend Issues

**Issue: Module not found**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue: CORS errors**
- Check that backend is running on port 8000
- Verify ALLOWED_ORIGINS in backend/.env includes http://localhost:5173

**Issue: API requests failing**
- Check browser console for errors
- Verify backend is running and accessible
- Check network tab in browser dev tools

### Docker Issues

**Issue: Port already in use**
```bash
# Find and kill process using the port
# On macOS/Linux:
lsof -ti:5432 | xargs kill -9  # PostgreSQL
lsof -ti:6379 | xargs kill -9  # Redis

# On Windows:
netstat -ano | findstr :5432
taskkill /PID <PID> /F
```

**Issue: Docker containers not starting**
```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

## Development Workflow

### Adding New Features

1. **Backend:**
   - Create model in `app/models/`
   - Create schema in `app/schemas/`
   - Create API routes in `app/api/`
   - Generate migration: `alembic revision --autogenerate -m "..."`
   - Apply migration: `alembic upgrade head`

2. **Frontend:**
   - Create service in `src/services/`
   - Create store in `src/store/` (if needed)
   - Create components in `src/features/`
   - Add routes in `src/App.jsx`

### Code Style

**Backend (Python):**
```bash
# Format code with black
black app/

# Lint with flake8
flake8 app/
```

**Frontend (JavaScript):**
```bash
# Format with prettier
npm run format

# Lint with ESLint
npm run lint
```

## What's Next?

This is **Phase 1 - Foundation** with authentication and basic infrastructure.

**Coming in Phase 1 (Weeks 2-4):**
- Posts list UI with filters
- Create post form
- Map view with Leaflet
- Matches UI
- SMS integration
- Spanish i18n

**Future Phases:**
- **Phase 2 (Weeks 5-8):** Volunteer Scheduling
- **Phase 3 (Weeks 9-10):** Pantry Locator
- **Phase 4 (Weeks 11-14):** Pods/Micro-Circles
- **Phase 5 (Weeks 15-16):** Polish & Public Launch

See [quick_start_roadmap.md](quick_start_roadmap.md) for the complete plan.

## Support

- **Documentation:** See README.md
- **API Docs:** http://localhost:8000/api/docs (when running)
- **GitHub Issues:** For bugs and feature requests

Happy building! 🚀
