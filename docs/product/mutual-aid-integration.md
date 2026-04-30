# Mutual Aid Integration Notes

Source preserved at `modules/mutual-aid/`.

Candidate features to integrate into DECLuTTER:

- Needs and offers board for decluttered items.
- Resource locator for donation, shelter, healthcare, and local support resources.
- Pods/micro-circles for sustained support.
- Volunteer scheduling later, after the core declutter/trade loop is stable.

Technical note: the source module uses React/Vite plus FastAPI/PostgreSQL/PostGIS/Celery/Redis. Treat it as a reference implementation and extract APIs deliberately into the existing DECLuTTER app/server architecture.
