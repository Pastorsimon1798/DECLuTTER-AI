# Launch Script Guide

This project includes helper scripts to easily launch the MutualCircle application from your desktop.

## Quick Launch Options

### Option 1: Shell Script (Recommended)

**For macOS/Linux:**

1. Double-click `launch.sh` in Finder, or
2. Run from terminal:
   ```bash
   ./launch.sh
   ```

The script will:
- ✅ Check all prerequisites (Python, Node.js, Docker)
- ✅ Set up backend virtual environment and dependencies
- ✅ Set up frontend dependencies
- ✅ Start Docker containers (PostgreSQL & Redis)
- ✅ Run database migrations
- ✅ Launch both backend and frontend servers
- ✅ Open the application in your browser

**What you'll see:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs

### Option 2: Manual Launch

If you prefer to launch services manually:

1. **Start Docker services:**
   ```bash
   docker-compose up -d
   ```

2. **Backend (in one terminal):**
   ```bash
   cd backend
   source venv/bin/activate  # or: python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.main
   ```

3. **Frontend (in another terminal):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## First-Time Setup

The launch script automatically handles first-time setup:

1. **Creates Python virtual environment** (if it doesn't exist)
2. **Installs Python dependencies** (if not already installed)
3. **Installs Node.js dependencies** (if not already installed)
4. **Creates `.env` file** with secure defaults (if it doesn't exist)
5. **Starts Docker containers** for PostgreSQL and Redis
6. **Runs database migrations**

## Configuration

### Environment Variables

The script automatically creates a `.env` file in the `backend/` directory with:
- Secure randomly generated `SECRET_KEY`
- Default database connection strings
- Development-friendly settings

To customize, edit `backend/.env` after first launch.

### Ports

- **Frontend:** 5173 (Vite default)
- **Backend API:** 8000
- **PostgreSQL:** 5432
- **Redis:** 6379

If these ports are in use, you'll need to:
1. Stop the conflicting services, or
2. Update the ports in:
   - `docker-compose.yml` (for PostgreSQL/Redis)
   - `frontend/vite.config.js` (for frontend)
   - `backend/app/main.py` (for backend)

## Troubleshooting

### "Docker is not running"
- Make sure Docker Desktop is installed and running
- The script will try to start it automatically on macOS

### "Port already in use"
- Stop other services using the ports
- Or change the ports in configuration files

### "Permission denied" when running launch.sh
- Make the script executable:
  ```bash
  chmod +x launch.sh
  ```

### Database connection errors
- Ensure Docker containers are running: `docker-compose ps`
- Check logs: `docker-compose logs db`

### Module not found errors
- Backend: Make sure virtual environment is activated and dependencies are installed
- Frontend: Run `npm install` in the `frontend/` directory

## Stopping the Application

Press `Ctrl+C` in the terminal where the script is running, or close the terminal window.

To stop Docker containers:
```bash
docker-compose down
```

## Advanced Usage

### Running in Background

To run the application in the background:

```bash
nohup ./launch.sh > launch.log 2>&1 &
```

### Viewing Logs

Backend logs appear in the terminal. For Docker logs:
```bash
docker-compose logs -f
```

### Resetting Everything

To start fresh:

```bash
# Stop everything
docker-compose down -v

# Remove virtual environment
rm -rf backend/venv

# Remove node_modules
rm -rf frontend/node_modules

# Run launch script again
./launch.sh
```

## Next Steps

After launching:
1. Visit http://localhost:5173
2. Register a new account
3. Explore the features:
   - Create posts (needs/offers)
   - Browse resources
   - Join/create pods
   - Schedule volunteer shifts

Happy coding! 🚀

