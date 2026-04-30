# Integrated Mutual Aid Platform
**Combining 4 Core Projects into One Cohesive System**

**Report Date:** November 11, 2025  
**Platform Name:** CommunityCircle (or your choice)  
**Timeline:** 12-16 weeks to full MVP  

---

## Executive Summary

This document provides a complete blueprint for building an integrated mutual aid platform that combines:

1. **Project 1:** SMS-to-Web Needs & Offers Board (Core Matching)
2. **Project 3:** Volunteer Scheduling + SMS Reminders (Coordination)
3. **Project 2:** Pods/Micro-Circles (Sustained Community)
4. **Project 10:** Pantry Locator (Discovery)

**Why These Four Work Together:**

```
Discovery (P10) → Matching (P1) → Coordination (P3) → Community (P2)
     ↓              ↓                 ↓                  ↓
"Find help"   "Post need/offer"  "Schedule help"   "Ongoing support"
```

**User Journey:**
1. Maria finds local food pantries via **Pantry Locator**
2. Sees she can also post a need for transportation via **Needs/Offers Board**
3. David volunteers to help, uses **Scheduling** to coordinate weekly grocery trips
4. They form a **Pod** with 3 other neighbors for ongoing mutual support

**Key Integration Points:**
- **Shared user accounts** across all 4 features
- **Unified notifications** (SMS/email for all events)
- **Common location/geohash** system for proximity matching
- **Integrated dashboard** showing all activities in one place

---

## Part 1: Unified Architecture

### 1.1 Technology Stack (All Projects)

**Frontend (Single React PWA):**
```yaml
Framework: React 18 with Vite
UI Library: Tailwind CSS + shadcn/ui components
Routing: React Router v6
State Management: Zustand (lightweight, simple)
Maps: Leaflet (for both Needs/Offers and Pantry Locator)
Offline: Workbox service worker + IndexedDB
i18n: i18next (English/Spanish/+)
Forms: React Hook Form + Zod validation
Calendar: React Big Calendar (for scheduling)
```

**Backend (Single FastAPI Application):**
```yaml
Framework: FastAPI (Python 3.11+)
Database: PostgreSQL 16 with PostGIS
ORM: SQLAlchemy 2.0 with async support
Migrations: Alembic
Background Jobs: Celery + Redis
Auth: FastAPI-Users (JWT + session)
API Docs: Auto-generated OpenAPI/Swagger
Testing: pytest + pytest-asyncio
```

**Infrastructure:**
```yaml
Database: PostgreSQL 16 + PostGIS + pgcrypto
Cache/Queue: Redis 7
File Storage: MinIO (S3-compatible, self-hosted)
SMS: Plivo (cheaper than Twilio)
Email: Brevo (free tier: 300/day)
Deployment: Docker Compose (local) + Fly.io (production)
Monitoring: Sentry (errors) + Posthog (analytics)
```

**Why This Stack:**
- **Single codebase** reduces maintenance burden
- **FastAPI** handles all features efficiently (REST + WebSocket for real-time)
- **PostgreSQL** powerful enough for all data needs (relational + geospatial + JSON)
- **React PWA** works offline and installs like native app
- **Total cost:** $20-50/month for 100-500 users

---

### 1.2 Unified Database Schema

This schema serves all 4 projects with shared tables and feature-specific extensions.

```sql
-- ============================================
-- SHARED / AUTHENTICATION TABLES
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pseudonym VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) UNIQUE, -- Optional for SMS-only users
  phone_hash VARCHAR(64) UNIQUE, -- Hashed phone number
  phone_verified BOOLEAN DEFAULT FALSE,
  locale VARCHAR(5) DEFAULT 'en', -- en, es, zh, etc.
  timezone VARCHAR(50) DEFAULT 'America/New_York',
  notification_prefs JSONB DEFAULT '{"sms": true, "email": true, "push": false}',
  location_geohash VARCHAR(12), -- User's general area (privacy-protected)
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_geohash ON users USING btree(location_geohash);
CREATE INDEX idx_users_phone_hash ON users(phone_hash);

-- User profiles (optional, enriched info)
CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  bio TEXT,
  skills TEXT[], -- ['cooking', 'driving', 'childcare']
  languages VARCHAR(5)[], -- ['en', 'es']
  accessibility_needs TEXT[],
  avatar_url VARCHAR(500),
  pronouns VARCHAR(20),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- PROJECT 1: NEEDS & OFFERS BOARD
-- ============================================

CREATE TABLE posts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type VARCHAR(10) NOT NULL CHECK (type IN ('NEED', 'OFFER')),
  category VARCHAR(50) NOT NULL, -- 'food', 'transport', 'housing', 'childcare', etc.
  title VARCHAR(200) NOT NULL,
  description TEXT,
  location_geohash VARCHAR(12) NOT NULL, -- Privacy-protected location
  location_point GEOGRAPHY(POINT, 4326), -- Actual lat/lon for distance calc (internal only)
  radius_meters INT DEFAULT 1000, -- How far willing to go for NEED or can provide OFFER
  author_id UUID NOT NULL REFERENCES users(id),
  visibility VARCHAR(20) DEFAULT 'public' CHECK (visibility IN ('public', 'circles', 'private')),
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'matched', 'in_progress', 'completed', 'cancelled')),
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_posts_geohash ON posts USING btree(location_geohash);
CREATE INDEX idx_posts_type ON posts(type);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_category ON posts(category);
CREATE INDEX idx_posts_location ON posts USING GIST(location_point);
CREATE INDEX idx_posts_expires ON posts(expires_at) WHERE status = 'open';

-- Matches between needs and offers
CREATE TABLE matches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  post_id UUID NOT NULL REFERENCES posts(id),
  responder_id UUID NOT NULL REFERENCES users(id),
  requester_id UUID NOT NULL REFERENCES users(id), -- Denormalized for easy queries
  method VARCHAR(20) DEFAULT 'in_app' CHECK (method IN ('in_app', 'sms', 'phone')),
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'completed', 'cancelled')),
  notes TEXT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_matches_post ON matches(post_id);
CREATE INDEX idx_matches_responder ON matches(responder_id);
CREATE INDEX idx_matches_requester ON matches(requester_id);

-- Contact tokens (for consented sharing of real contact info)
CREATE TABLE contact_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id),
  kind VARCHAR(20) NOT NULL CHECK (kind IN ('phone', 'email', 'signal', 'whatsapp')),
  encrypted_value TEXT NOT NULL, -- Encrypted contact info
  shared_with_user UUID REFERENCES users(id), -- Who has access
  shared_via_post UUID REFERENCES posts(id), -- Context of sharing
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contact_tokens_user ON contact_tokens(user_id);
CREATE INDEX idx_contact_tokens_shared_with ON contact_tokens(shared_with_user);

-- ============================================
-- PROJECT 3: VOLUNTEER SCHEDULING
-- ============================================

CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL,
  description TEXT,
  location_geohash VARCHAR(12),
  location_point GEOGRAPHY(POINT, 4326),
  address TEXT,
  phone VARCHAR(20),
  email VARCHAR(255),
  website VARCHAR(500),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE shifts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID REFERENCES organizations(id),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  location VARCHAR(500), -- Can be different from org location
  location_point GEOGRAPHY(POINT, 4326),
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  capacity INT NOT NULL DEFAULT 1, -- How many volunteers needed
  filled_count INT DEFAULT 0, -- Current sign-ups
  recurrence_rule TEXT, -- RRULE format for recurring shifts
  reminder_24h BOOLEAN DEFAULT TRUE,
  reminder_2h BOOLEAN DEFAULT TRUE,
  coordinator_id UUID REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('draft', 'open', 'full', 'completed', 'cancelled')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shifts_start ON shifts(start_time);
CREATE INDEX idx_shifts_org ON shifts(organization_id);
CREATE INDEX idx_shifts_status ON shifts(status);

CREATE TABLE shift_signups (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  shift_id UUID NOT NULL REFERENCES shifts(id) ON DELETE CASCADE,
  volunteer_id UUID NOT NULL REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled', 'no_show', 'completed')),
  notes TEXT,
  reminder_24h_sent BOOLEAN DEFAULT FALSE,
  reminder_2h_sent BOOLEAN DEFAULT FALSE,
  signed_up_at TIMESTAMPTZ DEFAULT NOW(),
  cancelled_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  UNIQUE(shift_id, volunteer_id)
);

CREATE INDEX idx_signups_shift ON shift_signups(shift_id);
CREATE INDEX idx_signups_volunteer ON shift_signups(volunteer_id);
CREATE INDEX idx_signups_status ON shift_signups(status);

-- ============================================
-- PROJECT 2: PODS (MICRO-CIRCLES)
-- ============================================

CREATE TABLE pods (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(200) NOT NULL,
  description TEXT,
  invite_code VARCHAR(20) UNIQUE NOT NULL,
  visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'friends_of_friends', 'public')),
  max_members INT DEFAULT 12,
  location_geohash VARCHAR(12), -- Approximate pod location
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pods_invite_code ON pods(invite_code);

CREATE TABLE pod_memberships (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pod_id UUID NOT NULL REFERENCES pods(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),
  role VARCHAR(50) DEFAULT 'member', -- 'member', 'steward', 'driver', 'phone_friend'
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  last_active_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(pod_id, user_id)
);

CREATE INDEX idx_pod_memberships_pod ON pod_memberships(pod_id);
CREATE INDEX idx_pod_memberships_user ON pod_memberships(user_id);

-- Pod posts (needs/updates within the pod)
CREATE TABLE pod_posts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pod_id UUID NOT NULL REFERENCES pods(id) ON DELETE CASCADE,
  author_id UUID NOT NULL REFERENCES users(id),
  type VARCHAR(20) NOT NULL CHECK (type IN ('need', 'offer', 'update', 'sos')),
  title VARCHAR(200),
  text TEXT NOT NULL,
  claimed_by UUID REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'claimed', 'completed', 'cancelled')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_pod_posts_pod ON pod_posts(pod_id);
CREATE INDEX idx_pod_posts_type ON pod_posts(type);
CREATE INDEX idx_pod_posts_status ON pod_posts(status);

-- Check-in schedules for pods
CREATE TABLE check_in_schedules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pod_id UUID NOT NULL REFERENCES pods(id) ON DELETE CASCADE,
  frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'custom')),
  time_of_day TIME NOT NULL DEFAULT '09:00:00',
  days_of_week INT[] DEFAULT ARRAY[1,2,3,4,5], -- 1=Mon, 7=Sun
  question TEXT DEFAULT 'How are you doing today?',
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE check_in_responses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  schedule_id UUID NOT NULL REFERENCES check_in_schedules(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),
  response TEXT,
  sentiment VARCHAR(20), -- 'positive', 'neutral', 'negative' (optional NLP)
  responded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_check_ins_schedule ON check_in_responses(schedule_id);
CREATE INDEX idx_check_ins_user ON check_in_responses(user_id);

-- ============================================
-- PROJECT 10: PANTRY LOCATOR
-- ============================================

-- Cache of 211 API data (to reduce API calls and work offline)
CREATE TABLE resource_listings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  external_id VARCHAR(200) UNIQUE, -- ID from 211 API
  name VARCHAR(300) NOT NULL,
  category VARCHAR(50) NOT NULL, -- 'food_pantry', 'shelter', 'medical', etc.
  description TEXT,
  location_address TEXT,
  location_point GEOGRAPHY(POINT, 4326),
  location_geohash VARCHAR(12),
  phone VARCHAR(20),
  email VARCHAR(255),
  website VARCHAR(500),
  hours JSONB, -- Structured hours data
  services TEXT[],
  languages VARCHAR(5)[],
  accessibility_features TEXT[],
  eligibility_requirements TEXT,
  documents_required TEXT[],
  last_verified_at TIMESTAMPTZ,
  cached_at TIMESTAMPTZ DEFAULT NOW(),
  cache_expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days'
);

CREATE INDEX idx_resources_geohash ON resource_listings(location_geohash);
CREATE INDEX idx_resources_category ON resource_listings(category);
CREATE INDEX idx_resources_location ON resource_listings USING GIST(location_point);

-- User bookmarks for resources
CREATE TABLE resource_bookmarks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  resource_id UUID NOT NULL REFERENCES resource_listings(id),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, resource_id)
);

-- ============================================
-- SHARED TABLES FOR ALL PROJECTS
-- ============================================

-- Unified notifications table
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL, -- 'match_found', 'shift_reminder', 'pod_sos', etc.
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,
  action_url VARCHAR(500), -- Deep link into app
  channels VARCHAR(20)[] DEFAULT ARRAY['in_app'], -- ['in_app', 'sms', 'email', 'push']
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'read')),
  sent_at TIMESTAMPTZ,
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created ON notifications(created_at);

-- Generic reports/flags for moderation
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  reporter_id UUID NOT NULL REFERENCES users(id),
  reported_user_id UUID REFERENCES users(id),
  reported_post_id UUID REFERENCES posts(id),
  reported_pod_post_id UUID REFERENCES pod_posts(id),
  reason VARCHAR(50) NOT NULL, -- 'spam', 'harassment', 'inappropriate', 'other'
  description TEXT,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'investigating', 'resolved', 'dismissed')),
  resolved_by UUID REFERENCES users(id),
  resolved_at TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_reporter ON reports(reporter_id);

-- Activity log for analytics (privacy-safe)
CREATE TABLE activity_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Nullable for privacy
  event_type VARCHAR(50) NOT NULL, -- 'post_created', 'shift_signup', 'pod_joined'
  event_data JSONB, -- Minimal, anonymized context
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_log_type ON activity_log(event_type);
CREATE INDEX idx_activity_log_created ON activity_log(created_at);
```

---

### 1.3 Application Structure

**Backend (FastAPI) - Directory Layout:**

```
backend/
├── alembic/              # Database migrations
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app initialization
│   ├── config.py         # Environment config
│   ├── database.py       # SQLAlchemy setup
│   │
│   ├── models/           # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py       # Needs/Offers
│   │   ├── shift.py      # Scheduling
│   │   ├── pod.py        # Pods
│   │   ├── resource.py   # Pantry Locator
│   │   └── notification.py
│   │
│   ├── schemas/          # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── shift.py
│   │   ├── pod.py
│   │   └── resource.py
│   │
│   ├── api/              # API routes
│   │   ├── __init__.py
│   │   ├── auth.py       # Login, register, verify
│   │   ├── posts.py      # Needs/Offers CRUD
│   │   ├── matches.py    # Matching logic
│   │   ├── shifts.py     # Scheduling
│   │   ├── pods.py       # Pod management
│   │   ├── resources.py  # Pantry locator
│   │   ├── sms.py        # SMS webhook handler
│   │   └── notifications.py
│   │
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── matching.py   # Find matches for needs/offers
│   │   ├── geohash.py    # Location privacy
│   │   ├── scheduler.py  # Shift reminder logic
│   │   ├── pod_manager.py
│   │   ├── two11_client.py  # 211 API integration
│   │   └── sms_service.py   # Plivo wrapper
│   │
│   ├── tasks/            # Celery background tasks
│   │   ├── __init__.py
│   │   ├── reminders.py  # Shift reminders
│   │   ├── check_ins.py  # Pod check-ins
│   │   ├── expiry.py     # Auto-expire old posts
│   │   └── cache_refresh.py  # Refresh 211 cache
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py   # Password hashing, JWT
│       ├── validators.py
│       └── helpers.py
│
├── tests/
│   ├── test_api/
│   ├── test_services/
│   └── test_tasks/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

**Frontend (React) - Directory Layout:**

```
frontend/
├── public/
│   ├── index.html
│   ├── manifest.json    # PWA manifest
│   └── service-worker.js
│
├── src/
│   ├── main.jsx         # App entry point
│   ├── App.jsx          # Root component with routing
│   │
│   ├── components/      # Reusable UI components
│   │   ├── layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Footer.jsx
│   │   │   └── MobileNav.jsx
│   │   │
│   │   ├── ui/          # shadcn/ui components
│   │   │   ├── Button.jsx
│   │   │   ├── Card.jsx
│   │   │   ├── Input.jsx
│   │   │   ├── Dialog.jsx
│   │   │   └── ...
│   │   │
│   │   └── shared/
│   │       ├── LocationPicker.jsx  # Used by all features
│   │       ├── MapView.jsx
│   │       ├── NotificationBadge.jsx
│   │       └── LoadingSpinner.jsx
│   │
│   ├── features/        # Feature-specific components
│   │   │
│   │   ├── posts/       # Project 1: Needs/Offers Board
│   │   │   ├── PostList.jsx
│   │   │   ├── PostCard.jsx
│   │   │   ├── CreatePostModal.jsx
│   │   │   ├── PostDetailPage.jsx
│   │   │   └── MatchesView.jsx
│   │   │
│   │   ├── shifts/      # Project 3: Scheduling
│   │   │   ├── ShiftCalendar.jsx
│   │   │   ├── ShiftCard.jsx
│   │   │   ├── CreateShiftModal.jsx
│   │   │   ├── MyShiftsPage.jsx
│   │   │   └── ShiftDetailPage.jsx
│   │   │
│   │   ├── pods/        # Project 2: Pods
│   │   │   ├── PodList.jsx
│   │   │   ├── PodCard.jsx
│   │   │   ├── CreatePodModal.jsx
│   │   │   ├── PodDetailPage.jsx
│   │   │   ├── PodPostList.jsx
│   │   │   ├── CheckInWidget.jsx
│   │   │   └── SOSButton.jsx
│   │   │
│   │   ├── resources/   # Project 10: Pantry Locator
│   │   │   ├── ResourceSearch.jsx
│   │   │   ├── ResourceList.jsx
│   │   │   ├── ResourceCard.jsx
│   │   │   ├── ResourceMap.jsx
│   │   │   └── ResourceDetailPage.jsx
│   │   │
│   │   ├── auth/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── PhoneVerification.jsx
│   │   │
│   │   └── dashboard/
│   │       ├── DashboardPage.jsx  # Unified view of all features
│   │       ├── ActivityFeed.jsx
│   │       └── QuickActions.jsx
│   │
│   ├── hooks/           # Custom React hooks
│   │   ├── useAuth.js
│   │   ├── useGeolocation.js
│   │   ├── useNotifications.js
│   │   └── useOfflineSync.js
│   │
│   ├── store/           # Zustand state management
│   │   ├── authStore.js
│   │   ├── postsStore.js
│   │   ├── shiftsStore.js
│   │   ├── podsStore.js
│   │   └── notificationsStore.js
│   │
│   ├── services/        # API clients
│   │   ├── api.js       # Axios instance with interceptors
│   │   ├── authService.js
│   │   ├── postsService.js
│   │   ├── shiftsService.js
│   │   ├── podsService.js
│   │   └── resourcesService.js
│   │
│   ├── utils/
│   │   ├── geohash.js
│   │   ├── date.js      # Date formatting
│   │   ├── distance.js  # Calculate distances
│   │   └── validators.js
│   │
│   ├── locales/         # i18n translations
│   │   ├── en.json
│   │   ├── es.json
│   │   └── index.js
│   │
│   └── styles/
│       ├── globals.css  # Tailwind imports
│       └── theme.js     # Design tokens
│
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

---

### 1.4 Unified User Experience

**Single App, Four Features Seamlessly Integrated:**

```
┌─────────────────────────────────────────┐
│  CommunityCircle                    🔔 3│
├─────────────────────────────────────────┤
│                                         │
│  🏠 Dashboard                           │
│  ─────────────────────────────────────  │
│  📌 Your Activity:                      │
│  • 2 active needs posted                │
│  • 1 upcoming volunteer shift (Wed)     │
│  • 3 pod check-ins this week            │
│  • 5 saved pantries nearby              │
│                                         │
│  ─────────────────────────────────────  │
│  🎯 Quick Actions:                      │
│  [Post Need] [Find Help] [Schedule]    │
│                                         │
├─────────────────────────────────────────┤
│  Bottom Nav:                            │
│  🏠 Home  📍 Find  🤝 Connect  👥 Pods  │
└─────────────────────────────────────────┘
```

**Navigation Structure:**

1. **🏠 Home (Dashboard)**
   - Unified activity feed
   - Quick actions for all features
   - Notifications center

2. **📍 Find**
   - **Tab 1:** Needs & Offers Board (Project 1)
   - **Tab 2:** Pantry Locator (Project 10)
   - **Tab 3:** Volunteer Shifts (Project 3)

3. **🤝 Connect**
   - My posts (needs/offers)
   - My matches
   - My volunteer shifts
   - Messages/notifications

4. **👥 Pods**
   - My pods list
   - Create/join pod
   - Pod activity feed
   - Check-ins

**Integrated User Flows:**

**Flow 1: From Discovery to Community**
```
1. User searches Pantry Locator → finds food pantry
2. Sees "Post a need" CTA → creates need for transportation
3. Volunteer matches → they coordinate via Scheduling
4. After 3 successful trips → coordinator suggests joining a Pod
5. Now part of sustained mutual support network
```

**Flow 2: Volunteer Journey**
```
1. User signs up for volunteer shift at food pantry
2. At shift, learns about Needs & Offers Board
3. Posts offer: "Can give rides to appointments"
4. Gets matched with elderly neighbor
5. Forms Pod with neighbor + 2 other local helpers
```

---

## Part 2: Phased Implementation Plan

### Phase 1: Foundation (Weeks 1-4) - Project 1 + Core Infrastructure

**Goal:** Build core platform with Needs & Offers Board operational.

**Week 1: Setup & Authentication**
- [ ] Setup mono-repo with FastAPI + React
- [ ] Database schema (all tables, migrations)
- [ ] User authentication (register, login, JWT)
- [ ] Phone verification (SMS OTP)
- [ ] Basic React app shell with routing

**Week 2: Project 1 - Needs & Offers (Backend)**
- [ ] CRUD API for posts (needs/offers)
- [ ] Geohash-based search
- [ ] Matching logic (distance + category)
- [ ] Contact token system (consented sharing)
- [ ] SMS webhook handler (Plivo)
- [ ] SMS commands: NEED, OFFER, FIND

**Week 3: Project 1 - Needs & Offers (Frontend)**
- [ ] Post list component with filters
- [ ] Create post form (web + mobile)
- [ ] Map view with geohash bubbles
- [ ] Post detail page
- [ ] Match notification system
- [ ] Contact sharing modal

**Week 4: Testing & Launch**
- [ ] End-to-end testing
- [ ] Accessibility audit (WCAG AA)
- [ ] Spanish translations (i18n)
- [ ] Deploy to Fly.io
- [ ] Beta test with 10 users

**Deliverables:**
✅ Working Needs & Offers Board (web + SMS)  
✅ User authentication  
✅ Core platform infrastructure  
✅ 10 beta users actively posting  

---

### Phase 2: Coordination (Weeks 5-8) - Project 3 (Volunteer Scheduling)

**Goal:** Add volunteer scheduling with automated reminders.

**Week 5: Scheduling Backend**
- [ ] Organizations table + API
- [ ] Shifts CRUD API
- [ ] Shift signups API
- [ ] Celery setup for background jobs
- [ ] Reminder tasks (24h, 2h before shift)

**Week 6: Scheduling Frontend**
- [ ] Shift calendar view (React Big Calendar)
- [ ] Shift detail page with sign-up
- [ ] My shifts dashboard
- [ ] Create shift form (for coordinators)
- [ ] Cancel/reschedule flows

**Week 7: Integration & Notifications**
- [ ] Unified notifications table
- [ ] SMS reminders via Plivo
- [ ] Email reminders via Brevo
- [ ] In-app notification center
- [ ] Link scheduling to needs/offers (e.g., "Help needed for shift")

**Week 8: Testing & Iteration**
- [ ] Test with 2 food pantries
- [ ] Measure no-show rate (goal: <5%)
- [ ] Feedback from coordinators
- [ ] Polish UI based on usage

**Deliverables:**
✅ Working volunteer scheduling system  
✅ Automated reminders (SMS + email)  
✅ 2 organizations using scheduling  
✅ Integrated with needs/offers board  

---

### Phase 3: Discovery (Weeks 9-10) - Project 10 (Pantry Locator)

**Goal:** Help users find existing resources.

**Week 9: 211 API Integration + Caching**
- [ ] 211 Open Referral API client
- [ ] Resource listings table + cache
- [ ] Search API (by location, category)
- [ ] Auto-refresh cache (weekly via Celery)
- [ ] Bookmark system

**Week 10: Pantry Locator Frontend**
- [ ] Resource search interface
- [ ] Map view with resource pins
- [ ] List view with filters (open now, distance)
- [ ] Resource detail page (hours, contact, directions)
- [ ] Bookmark favorites
- [ ] "Post a need here" CTA (link to Project 1)

**Deliverables:**
✅ Working pantry/resource locator  
✅ Integrated with 211 Open Referral API  
✅ Cached data for offline access  
✅ Seamless connection to needs/offers board  

---

### Phase 4: Community (Weeks 11-14) - Project 2 (Pods)

**Goal:** Build sustained mutual support through micro-circles.

**Week 11: Pods Backend**
- [ ] Pods CRUD API
- [ ] Pod memberships API
- [ ] Invite code generation
- [ ] Pod posts (internal needs/offers/updates)
- [ ] Check-in schedules setup

**Week 12: Pods Frontend (Core)**
- [ ] Pod list view
- [ ] Create pod modal
- [ ] Join via invite code/link
- [ ] Pod detail page
- [ ] Member management
- [ ] Pod settings

**Week 13: Pods Frontend (Advanced)**
- [ ] Pod post feed (internal needs/offers)
- [ ] Check-in widget
- [ ] SOS button (emergency broadcast)
- [ ] Role assignment UI
- [ ] Activity timeline

**Week 14: Integration & Polish**
- [ ] Connect pods to main needs/offers board (opt-in)
- [ ] Celery task for automated check-ins
- [ ] Wellness alerts (missed check-ins)
- [ ] Pod analytics dashboard
- [ ] Final testing with 5 pilot pods

**Deliverables:**
✅ Working pods/micro-circles feature  
✅ Automated check-ins  
✅ SOS emergency system  
✅ 5 active pods with regular check-ins  

---

### Phase 5: Polish & Launch (Weeks 15-16)

**Week 15: User Experience Polish**
- [ ] Unified dashboard (activity feed from all 4 features)
- [ ] Onboarding flow (5-step wizard)
- [ ] Help center (FAQ, videos)
- [ ] Accessibility improvements
- [ ] Performance optimization

**Week 16: Public Launch**
- [ ] Marketing materials (website, flyers)
- [ ] Community partnerships (3-5 orgs)
- [ ] Press release
- [ ] Public beta launch
- [ ] Monitoring and support

**Final Deliverables:**
✅ Integrated platform with all 4 features  
✅ 50+ active users  
✅ 5+ organizations using  
✅ English + Spanish full support  
✅ Offline-first PWA  

---

## Part 3: Key Integration Points

### 3.1 Unified Notifications System

All four projects share a single notification system:

**Backend (Notification Service):**

```python
# app/services/notification_service.py

from enum import Enum
from typing import List, Optional
from datetime import datetime

class NotificationType(Enum):
    # Project 1: Needs/Offers
    MATCH_FOUND = "match_found"
    MATCH_ACCEPTED = "match_accepted"
    MATCH_COMPLETED = "match_completed"
    POST_EXPIRING = "post_expiring"
    
    # Project 3: Scheduling
    SHIFT_REMINDER_24H = "shift_reminder_24h"
    SHIFT_REMINDER_2H = "shift_reminder_2h"
    SHIFT_CANCELLED = "shift_cancelled"
    SHIFT_COMPLETED = "shift_completed"
    
    # Project 2: Pods
    POD_INVITATION = "pod_invitation"
    POD_CHECK_IN = "pod_check_in"
    POD_SOS = "pod_sos"
    POD_POST_REPLY = "pod_post_reply"
    POD_MISSED_CHECK_IN = "pod_missed_check_in"
    
    # General
    WELCOME = "welcome"
    VERIFICATION_CODE = "verification_code"

class NotificationService:
    def __init__(self, db, sms_service, email_service):
        self.db = db
        self.sms = sms_service
        self.email = email_service
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        action_url: Optional[str] = None,
        data: Optional[dict] = None
    ):
        """Send notification via user's preferred channels"""
        
        # Get user preferences
        user = await self.db.get_user(user_id)
        prefs = user.notification_prefs
        
        # Create notification record
        notification = await self.db.create_notification(
            user_id=user_id,
            type=notification_type.value,
            title=title,
            body=body,
            action_url=action_url,
            channels=[]
        )
        
        # Send via preferred channels
        if prefs.get('in_app', True):
            # Already created above
            notification.channels.append('in_app')
        
        if prefs.get('sms', False) and user.phone_verified:
            try:
                await self.sms.send(
                    to=user.phone,
                    message=f"{title}\n{body}\n{action_url or ''}"
                )
                notification.channels.append('sms')
            except Exception as e:
                print(f"SMS send failed: {e}")
        
        if prefs.get('email', True) and user.email:
            try:
                await self.email.send(
                    to=user.email,
                    subject=title,
                    body=body,
                    action_url=action_url
                )
                notification.channels.append('email')
            except Exception as e:
                print(f"Email send failed: {e}")
        
        # Update notification status
        notification.status = 'sent'
        notification.sent_at = datetime.now()
        await self.db.save(notification)
        
        return notification

# Usage examples:

# Project 1: New match found
await notification_service.send_notification(
    user_id=volunteer_id,
    notification_type=NotificationType.MATCH_FOUND,
    title="Someone needs your help!",
    body=f"{requester.pseudonym} needs {post.category} help nearby",
    action_url=f"/posts/{post.id}"
)

# Project 3: Shift reminder
await notification_service.send_notification(
    user_id=volunteer_id,
    notification_type=NotificationType.SHIFT_REMINDER_24H,
    title="Shift Reminder",
    body=f"Volunteering tomorrow at {shift.name} - {shift.start_time.strftime('%I:%M %p')}",
    action_url=f"/shifts/{shift.id}"
)

# Project 2: Pod SOS
pod_members = await get_pod_members(pod_id)
for member in pod_members:
    await notification_service.send_notification(
        user_id=member.user_id,
        notification_type=NotificationType.POD_SOS,
        title=f"🚨 SOS from {author.pseudonym}",
        body=sos_message,
        action_url=f"/pods/{pod_id}/posts/{post_id}"
    )
```

**Frontend (Unified Notification Center):**

```jsx
// src/components/shared/NotificationCenter.jsx

import { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { useNotifications } from '@/hooks/useNotifications';

export function NotificationCenter() {
  const { notifications, unreadCount, markAsRead } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="relative">
      {/* Bell icon with badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2"
      >
        <Bell size={24} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>
      
      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white shadow-lg rounded-lg z-50">
          <div className="p-4 border-b">
            <h3 className="font-semibold">Notifications</h3>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              notifications.map(notif => (
                <NotificationItem
                  key={notif.id}
                  notification={notif}
                  onRead={() => markAsRead(notif.id)}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function NotificationItem({ notification, onRead }) {
  const { type, title, body, action_url, created_at, status } = notification;
  
  // Icon based on type
  const icon = {
    'match_found': '🤝',
    'shift_reminder_24h': '📅',
    'pod_sos': '🚨',
    'pod_check_in': '💬',
  }[type] || '🔔';
  
  return (
    <div
      className={`p-4 border-b hover:bg-gray-50 cursor-pointer ${
        status === 'read' ? 'opacity-60' : ''
      }`}
      onClick={() => {
        onRead();
        if (action_url) {
          window.location.href = action_url;
        }
      }}
    >
      <div className="flex items-start gap-3">
        <div className="text-2xl">{icon}</div>
        <div className="flex-1">
          <h4 className="font-semibold text-sm">{title}</h4>
          <p className="text-sm text-gray-600 mt-1">{body}</p>
          <span className="text-xs text-gray-400 mt-2 block">
            {formatRelativeTime(created_at)}
          </span>
        </div>
        {status === 'pending' && (
          <div className="w-2 h-2 bg-blue-500 rounded-full" />
        )}
      </div>
    </div>
  );
}
```

---

### 3.2 Shared Geolocation System

All features use the same geohash-based location privacy system:

**Backend (Geohash Service):**

```python
# app/services/geohash_service.py

import geohash2 as geohash
from typing import Tuple, List

class GeohashService:
    """Privacy-preserving location service"""
    
    @staticmethod
    def encode_location(lat: float, lon: float, precision: int = 7) -> str:
        """
        Convert lat/lon to geohash
        Precision 7 = ~150m accuracy (good privacy/utility balance)
        """
        return geohash.encode(lat, lon, precision=precision)
    
    @staticmethod
    def decode_location(geohash_str: str) -> Tuple[float, float]:
        """Convert geohash back to lat/lon (center point)"""
        return geohash.decode(geohash_str)
    
    @staticmethod
    def get_neighbors(geohash_str: str) -> List[str]:
        """Get all 8 neighboring geohash cells"""
        return geohash.neighbors(geohash_str)
    
    @staticmethod
    def search_radius(center_hash: str, radius_meters: int) -> List[str]:
        """
        Get all geohash cells within radius
        Returns list of geohash prefixes to search
        """
        # Determine precision needed based on radius
        if radius_meters <= 200:
            precision = 7  # ~150m cells
        elif radius_meters <= 1000:
            precision = 6  # ~1.2km cells
        else:
            precision = 5  # ~5km cells
        
        # Truncate to appropriate precision
        center = center_hash[:precision]
        
        # Include center + all neighbors
        cells = [center] + geohash.neighbors(center)
        
        # For larger radii, may need 2nd ring of neighbors
        if radius_meters > 1000:
            all_cells = cells[:]
            for cell in cells:
                all_cells.extend(geohash.neighbors(cell))
            return list(set(all_cells))  # Deduplicate
        
        return cells

# Usage in all features:

# Project 1: Search nearby needs/offers
async def search_nearby_posts(user_location: dict, radius_m: int, category: str):
    user_hash = GeohashService.encode_location(
        user_location['lat'],
        user_location['lon']
    )
    
    search_hashes = GeohashService.search_radius(user_hash, radius_m)
    
    # Query database
    posts = await db.query(Post).filter(
        Post.location_geohash.startswith(any(search_hashes)),
        Post.category == category,
        Post.status == 'open'
    ).all()
    
    # Further filter by exact distance
    return [p for p in posts if calculate_distance(user_location, p.location) <= radius_m]

# Project 10: Search nearby resources (pantries)
async def search_nearby_resources(user_location: dict, radius_m: int):
    user_hash = GeohashService.encode_location(
        user_location['lat'],
        user_location['lon']
    )
    
    search_hashes = GeohashService.search_radius(user_hash, radius_m)
    
    resources = await db.query(ResourceListing).filter(
        ResourceListing.location_geohash.startswith(any(search_hashes)),
        ResourceListing.category == 'food_pantry'
    ).all()
    
    return resources
```

---

### 3.3 Unified Dashboard (Home Page)

The dashboard shows activity from all four features in one place:

```jsx
// src/features/dashboard/DashboardPage.jsx

import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { ActivityFeed } from './ActivityFeed';
import { QuickActions } from './QuickActions';
import { StatsCards } from './StatsCards';

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [activity, setActivity] = useState([]);
  
  useEffect(() => {
    fetchDashboardData();
  }, []);
  
  async function fetchDashboardData() {
    // Fetch aggregated data from all features
    const response = await fetch('/api/dashboard');
    const data = await response.json();
    
    setStats(data.stats);
    setActivity(data.activity);
  }
  
  return (
    <div className="max-w-6xl mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">
        Welcome back, {user.pseudonym}! 👋
      </h1>
      
      {/* Quick stats from all features */}
      <StatsCards
        activeNeeds={stats?.active_needs || 0}
        upcomingShifts={stats?.upcoming_shifts || 0}
        activePods={stats?.active_pods || 0}
        savedResources={stats?.saved_resources || 0}
      />
      
      {/* Quick actions */}
      <QuickActions />
      
      {/* Unified activity feed */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <ActivityFeed items={activity} />
      </div>
    </div>
  );
}

function StatsCards({ activeNeeds, upcomingShifts, activePods, savedResources }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <StatCard
        icon="📌"
        label="Active Needs/Offers"
        value={activeNeeds}
        link="/posts"
      />
      <StatCard
        icon="📅"
        label="Upcoming Shifts"
        value={upcomingShifts}
        link="/shifts"
      />
      <StatCard
        icon="👥"
        label="Your Pods"
        value={activePods}
        link="/pods"
      />
      <StatCard
        icon="📍"
        label="Saved Resources"
        value={savedResources}
        link="/resources"
      />
    </div>
  );
}

function ActivityFeed({ items }) {
  return (
    <div className="space-y-3">
      {items.map(item => (
        <ActivityItem key={item.id} item={item} />
      ))}
    </div>
  );
}

function ActivityItem({ item }) {
  // Different rendering based on type
  const config = {
    'post_created': {
      icon: '📌',
      color: 'blue',
      text: `You posted: "${item.title}"`
    },
    'match_found': {
      icon: '🤝',
      color: 'green',
      text: `${item.other_user} wants to help with "${item.title}"`
    },
    'shift_signup': {
      icon: '📅',
      color: 'purple',
      text: `You signed up for ${item.shift_name}`
    },
    'pod_check_in': {
      icon: '💬',
      color: 'yellow',
      text: `You checked in with ${item.pod_name}`
    },
    'resource_bookmarked': {
      icon: '⭐',
      color: 'orange',
      text: `You saved ${item.resource_name}`
    }
  }[item.type];
  
  return (
    <div className={`flex items-center gap-3 p-3 bg-${config.color}-50 rounded-lg`}>
      <div className="text-2xl">{config.icon}</div>
      <div className="flex-1">
        <p className="text-sm">{config.text}</p>
        <span className="text-xs text-gray-500">
          {formatRelativeTime(item.created_at)}
        </span>
      </div>
      <a href={item.link} className="text-sm text-blue-600 hover:underline">
        View →
      </a>
    </div>
  );
}
```

**Backend Dashboard API:**

```python
# app/api/dashboard.py

from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    """Get aggregated dashboard data from all features"""
    
    # Stats
    active_needs = await db.count(
        Post,
        filters={"author_id": current_user.id, "status": "open"}
    )
    
    upcoming_shifts = await db.count(
        ShiftSignup,
        filters={
            "volunteer_id": current_user.id,
            "status": "confirmed",
            "shift.start_time > NOW()"
        }
    )
    
    active_pods = await db.count(
        PodMembership,
        filters={"user_id": current_user.id}
    )
    
    saved_resources = await db.count(
        ResourceBookmark,
        filters={"user_id": current_user.id}
    )
    
    # Recent activity (from all features)
    activity = await db.query(ActivityLog).filter(
        ActivityLog.user_id == current_user.id
    ).order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()
    
    # Transform activity into unified format
    activity_items = []
    for log in activity:
        item = {
            "id": log.id,
            "type": log.event_type,
            "created_at": log.created_at,
            "link": None
        }
        
        # Add type-specific data
        if log.event_type == "post_created":
            post = await db.get(Post, log.event_data["post_id"])
            item["title"] = post.title
            item["link"] = f"/posts/{post.id}"
        
        elif log.event_type == "match_found":
            match = await db.get(Match, log.event_data["match_id"])
            post = await match.post
            other_user = await db.get(User, log.event_data["other_user_id"])
            item["title"] = post.title
            item["other_user"] = other_user.pseudonym
            item["link"] = f"/posts/{post.id}"
        
        elif log.event_type == "shift_signup":
            shift = await db.get(Shift, log.event_data["shift_id"])
            item["shift_name"] = shift.name
            item["link"] = f"/shifts/{shift.id}"
        
        # ... handle other types
        
        activity_items.append(item)
    
    return {
        "stats": {
            "active_needs": active_needs,
            "upcoming_shifts": upcoming_shifts,
            "active_pods": active_pods,
            "saved_resources": saved_resources
        },
        "activity": activity_items
    }
```

---

## Part 4: Technical Implementation Details

### 4.1 SMS Integration (Shared Across Projects)

All SMS commands are handled by a single webhook with intelligent routing:

```python
# app/api/sms.py

from fastapi import APIRouter, Form
from app.services.sms_handler import SMSHandler

router = APIRouter(prefix="/sms", tags=["sms"])

@router.post("/webhook")
async def handle_incoming_sms(
    From: str = Form(...),  # Phone number
    Body: str = Form(...),  # Message text
):
    """
    Unified SMS webhook handling all commands across features
    
    Commands:
    - NEED [category] [location] [description] - Project 1
    - OFFER [category] [location] [description] - Project 1
    - FIND [category] [location] - Project 1 + 10
    - SHIFTS - Project 3
    - POD [code] - Project 2
    - CHECK - Project 2
    - HELP - General
    """
    
    handler = SMSHandler()
    response = await handler.process_message(From, Body)
    
    return response.to_twiml()  # Return TwiML response

# app/services/sms_handler.py

class SMSHandler:
    async def process_message(self, phone: str, body: str):
        # Get or create user
        user = await self.get_user_by_phone(phone)
        
        # Parse command
        command = body.strip().upper().split()[0]
        
        # Route to appropriate handler
        if command == "NEED":
            return await self.handle_need(user, body)
        
        elif command == "OFFER":
            return await self.handle_offer(user, body)
        
        elif command == "FIND":
            return await self.handle_find(user, body)
        
        elif command == "SHIFTS":
            return await self.handle_shifts(user, body)
        
        elif command == "POD":
            return await self.handle_pod(user, body)
        
        elif command == "CHECK":
            return await self.handle_check_in(user, body)
        
        elif command == "HELP":
            return await self.handle_help(user)
        
        else:
            return SMSResponse(
                f"Unknown command '{command}'. Reply HELP for available commands."
            )
    
    async def handle_need(self, user, body):
        """Project 1: Create a need"""
        # Parse: NEED food 10001 Need groceries this week
        parts = body.split(maxsplit=3)
        
        if len(parts) < 4:
            return SMSResponse(
                "Format: NEED [category] [location] [description]\n"
                "Example: NEED food 10001 Need groceries"
            )
        
        _, category, location, description = parts
        
        # Create post
        post = await create_post(
            author_id=user.id,
            type="NEED",
            category=category,
            title=description[:200],
            description=description,
            location_geohash=geocode_location(location),
            radius_meters=2000
        )
        
        return SMSResponse(
            f"✅ Need posted! ID: {post.id[:8]}\n"
            f"We'll notify nearby helpers.\n"
            f"View: {APP_URL}/posts/{post.id}"
        )
    
    async def handle_shifts(self, user, body):
        """Project 3: List upcoming shifts"""
        shifts = await get_user_shifts(user.id, upcoming=True, limit=3)
        
        if not shifts:
            return SMSResponse(
                "No upcoming shifts.\n"
                f"Browse shifts: {APP_URL}/shifts"
            )
        
        message = "📅 Your upcoming shifts:\n\n"
        for shift in shifts:
            message += f"• {shift.name}\n"
            message += f"  {shift.start_time.strftime('%b %d at %I:%M %p')}\n"
            message += f"  {shift.location}\n\n"
        
        message += f"Manage: {APP_URL}/shifts"
        
        return SMSResponse(message)
    
    async def handle_pod(self, user, body):
        """Project 2: Join a pod"""
        # Parse: POD ABC123
        parts = body.split()
        
        if len(parts) != 2:
            return SMSResponse(
                "Format: POD [invite_code]\n"
                "Example: POD ABC123"
            )
        
        _, invite_code = parts
        
        # Find pod
        pod = await get_pod_by_invite_code(invite_code)
        
        if not pod:
            return SMSResponse(f"Pod not found with code '{invite_code}'")
        
        # Join pod
        await join_pod(pod.id, user.id)
        
        return SMSResponse(
            f"✅ You joined '{pod.name}'!\n"
            f"Members: {await count_pod_members(pod.id)}\n"
            f"View: {APP_URL}/pods/{pod.id}"
        )
    
    async def handle_check_in(self, user, body):
        """Project 2: Quick check-in"""
        # Parse: CHECK Doing well today!
        message = body[6:].strip() or "👍"
        
        # Get user's active pods
        pods = await get_user_pods(user.id)
        
        if not pods:
            return SMSResponse(
                "You're not in any pods yet.\n"
                f"Create or join one: {APP_URL}/pods"
            )
        
        # Post check-in to all pods
        for pod in pods:
            await create_pod_post(
                pod_id=pod.id,
                author_id=user.id,
                type="update",
                text=message
            )
        
        return SMSResponse(
            f"✅ Check-in posted to {len(pods)} pod(s)!\n"
            f"View: {APP_URL}/pods"
        )
```

---

### 4.2 Offline Support Strategy

**What Works Offline:**

| Feature | Offline Capability |
|---------|-------------------|
| **Project 1: Needs/Offers** | • View cached posts<br>• Create posts (queued)<br>• View map (cached tiles) |
| **Project 3: Scheduling** | • View your shifts (cached)<br>• Cancel shifts (queued)<br>• View calendar |
| **Project 2: Pods** | • View pod activity (cached)<br>• Post updates (queued)<br>• View members |
| **Project 10: Pantry Locator** | • View cached resources<br>• View saved bookmarks<br>• View map (cached) |

**Implementation (Service Worker):**

```javascript
// public/service-worker.js

const CACHE_NAME = 'communitycircle-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/css/main.css',
  '/static/js/bundle.js',
  '/offline.html'
];

// Install event: cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// Fetch event: serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // API requests: network-first strategy
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
  }
  
  // Static assets: cache-first strategy
  else {
    event.respondWith(cacheFirstStrategy(request));
  }
});

async function networkFirstStrategy(request) {
  try {
    // Try network first
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Network failed, try cache
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // No cache, return offline message
    return new Response(
      JSON.stringify({ error: 'Offline', cached: false }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

async function cacheFirstStrategy(request) {
  // Try cache first
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  // Cache miss, fetch from network
  try {
    const response = await fetch(request);
    
    // Cache for next time
    const cache = await caches.open(DYNAMIC_CACHE);
    cache.put(request, response.clone());
    
    return response;
  } catch (error) {
    // Network failed, return offline page
    return caches.match('/offline.html');
  }
}

// Background sync for queued actions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-queued-actions') {
    event.waitUntil(syncQueuedActions());
  }
});

async function syncQueuedActions() {
  // Get queued actions from IndexedDB
  const db = await openDB('offlineQueue');
  const queue = await db.getAll('actions');
  
  for (const action of queue) {
    try {
      // Retry API call
      const response = await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body
      });
      
      if (response.ok) {
        // Success! Remove from queue
        await db.delete('actions', action.id);
      }
    } catch (error) {
      // Still offline, will retry on next sync
      console.log('Sync failed, will retry:', error);
    }
  }
}
```

**Frontend: Offline Queue:**

```javascript
// src/utils/offlineQueue.js

import { openDB } from 'idb';

const DB_NAME = 'offlineQueue';
const STORE_NAME = 'actions';

export async function queueAction(action) {
  const db = await openDB(DB_NAME, 1, {
    upgrade(db) {
      db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
    }
  });
  
  await db.add(STORE_NAME, {
    ...action,
    timestamp: Date.now()
  });
  
  // Show user feedback
  showToast('⏳ Saved for when you\'re back online');
  
  // Request background sync
  if ('sync' in self.registration) {
    await self.registration.sync.register('sync-queued-actions');
  }
}

// Usage in API service:
export async function createPost(data) {
  try {
    const response = await fetch('/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    return await response.json();
  } catch (error) {
    // Offline - queue for later
    await queueAction({
      url: '/api/posts',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    // Return optimistic response
    return {
      id: 'temp-' + Date.now(),
      ...data,
      status: 'pending_sync'
    };
  }
}
```

---

## Part 5: Development Workflow & Best Practices

### 5.1 Git Workflow

```bash
# Branch structure
main                    # Production-ready code
├── develop             # Integration branch
├── feature/needs-board # Project 1
├── feature/scheduling  # Project 3
├── feature/pods        # Project 2
└── feature/locator     # Project 10

# Daily workflow
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
# ... make changes ...
git add .
git commit -m "feat(posts): add geohash search"
git push origin feature/my-feature
# ... create PR to develop ...
```

**Commit Message Convention:**
```
feat(scope): description     # New feature
fix(scope): description      # Bug fix
docs(scope): description     # Documentation
style(scope): description    # Formatting
refactor(scope): description # Code restructuring
test(scope): description     # Adding tests
chore(scope): description    # Maintenance

Examples:
feat(posts): add SMS command NEED
fix(shifts): reminder not sending
docs(api): update deployment guide
```

---

### 5.2 Testing Strategy

**Backend Testing (pytest):**

```python
# tests/test_api/test_posts.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_post():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Authenticate
        auth_response = await client.post("/api/auth/login", json={
            "phone": "+15551234567",
            "password": "testpass"
        })
        token = auth_response.json()["access_token"]
        
        # Create post
        response = await client.post(
            "/api/posts",
            json={
                "type": "NEED",
                "category": "food",
                "title": "Need groceries",
                "description": "Help with grocery shopping",
                "location": {"lat": 40.7128, "lon": -74.0060},
                "radius_meters": 1000
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "NEED"
        assert data["category"] == "food"
        assert "location_geohash" in data
        assert len(data["location_geohash"]) == 7  # Privacy protection

@pytest.mark.asyncio
async def test_search_nearby_posts():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/posts/search",
            params={
                "lat": 40.7128,
                "lon": -74.0060,
                "radius": 2000,
                "type": "NEED"
            }
        )
        
        assert response.status_code == 200
        posts = response.json()
        assert isinstance(posts, list)
        
        # Verify all results within radius
        for post in posts:
            distance = calculate_distance(
                (40.7128, -74.0060),
                (post["location"]["lat"], post["location"]["lon"])
            )
            assert distance <= 2000
```

**Frontend Testing (Vitest + React Testing Library):**

```jsx
// src/features/posts/__tests__/PostList.test.jsx

import { render, screen, waitFor } from '@testing-library/react';
import { PostList } from '../PostList';
import { vi } from 'vitest';

// Mock API
vi.mock('@/services/postsService', () => ({
  getPosts: vi.fn(() => Promise.resolve([
    {
      id: '1',
      type: 'NEED',
      title: 'Need groceries',
      category: 'food',
      author: { pseudonym: 'Alice' }
    }
  ]))
}));

describe('PostList', () => {
  it('renders list of posts', async () => {
    render(<PostList type="NEED" />);
    
    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for posts to load
    await waitFor(() => {
      expect(screen.getByText('Need groceries')).toBeInTheDocument();
    });
    
    // Should show author
    expect(screen.getByText('Alice')).toBeInTheDocument();
  });
  
  it('filters by category', async () => {
    render(<PostList type="NEED" category="food" />);
    
    await waitFor(() => {
      const posts = screen.getAllByTestId('post-card');
      expect(posts).toHaveLength(1);
    });
  });
});
```

---

### 5.3 Deployment Checklist

**Before Each Deploy:**

- [ ] All tests passing (`pytest` and `npm test`)
- [ ] Database migrations applied (`alembic upgrade head`)
- [ ] Environment variables set in production
- [ ] Secrets rotated (JWT secret, API keys)
- [ ] SSL/TLS certificates valid
- [ ] Monitoring configured (Sentry, Posthog)
- [ ] Backup taken of production database
- [ ] Rollback plan documented

**Deployment Commands:**

```bash
# Backend (Fly.io)
fly deploy --config fly.toml

# Frontend (Vercel or Fly.io)
npm run build
vercel --prod

# Or via Fly.io
fly deploy --config fly.frontend.toml

# Database migration (before deploy)
fly ssh console
alembic upgrade head
```

---

## Part 6: Success Metrics & Monitoring

### 6.1 Key Performance Indicators (KPIs)

**Project 1: Needs & Offers Board**
- Posts created per week (goal: 50+)
- Match rate (% of needs matched within 24h, goal: 70%+)
- Median time-to-match (goal: <6 hours)
- % of matches within 1 km (goal: 70%+)

**Project 3: Volunteer Scheduling**
- Shifts filled rate (goal: 90%+)
- No-show rate (goal: <5%)
- Volunteer retention (% still active after 3 months, goal: 60%+)
- Coordinator time saved (hours/week, goal: 5+)

**Project 2: Pods**
- Active pods with weekly activity (goal: 20+)
- Check-in response rate (goal: 80%+)
- Average pod lifespan (goal: 3+ months)
- SOS response time (goal: <15 minutes)

**Project 10: Pantry Locator**
- Searches per week (goal: 100+)
- Resources bookmarked (goal: 30%+ of searches)
- 211 API cache hit rate (goal: 80%+ to reduce costs)

**Overall Platform**
- Daily Active Users (goal: 100+ by month 6)
- Weekly Active Users (goal: 500+ by month 12)
- User retention (% returning after 1 week, goal: 50%+)
- Platform uptime (goal: 99.5%+)

---

### 6.2 Analytics Implementation

**Privacy-Safe Analytics (PostHog):**

```javascript
// src/utils/analytics.js

import posthog from 'posthog-js';

// Initialize (anonymized by default)
posthog.init(import.meta.env.VITE_POSTHOG_KEY, {
  api_host: 'https://app.posthog.com',
  
  // Privacy settings
  opt_out_capturing_by_default: false,
  respect_dnt: true,
  disable_session_recording: true, // No session replays
  property_blacklist: ['$current_url', '$pathname'], // Don't track URLs
  
  // Capture only aggregate events
  loaded: (posthog) => {
    if (import.meta.env.DEV) posthog.opt_out_capturing();
  }
});

// Track events (no personal data)
export function trackEvent(eventName, properties = {}) {
  // Remove any PII
  const safeProperties = {
    ...properties,
    // Only include aggregate data
    category: properties.category,
    type: properties.type,
    // Never include: names, emails, phone numbers, exact locations
  };
  
  posthog.capture(eventName, safeProperties);
}

// Usage:
trackEvent('post_created', { type: 'NEED', category: 'food' });
trackEvent('shift_signed_up', { shift_type: 'food_pantry' });
trackEvent('pod_joined', { pod_size: 5 });
```

**Backend Analytics (Activity Log):**

```python
# app/services/analytics.py

async def log_activity(
    user_id: Optional[str],
    event_type: str,
    event_data: dict
):
    """Log activity for analytics (privacy-safe)"""
    
    # Anonymize event data
    safe_data = {
        # Include only aggregate info
        'category': event_data.get('category'),
        'type': event_data.get('type'),
        # Never include PII
    }
    
    await db.create(ActivityLog, {
        'user_id': user_id,  # Can be NULL for anonymous
        'event_type': event_type,
        'event_data': safe_data
    })

# Usage:
await log_activity(
    user_id=current_user.id,
    event_type='post_created',
    event_data={'type': 'NEED', 'category': 'food'}
)
```

---

## Part 7: Next Steps & Resources

### 7.1 Week 1 Action Plan

**Day 1: Project Setup**
```bash
# Create repo
mkdir communitycircle
cd communitycircle
git init
git checkout -b develop

# Backend setup
mkdir backend
cd backend
python -m venv venv
source venv/bin/activate
pip install fastapi[all] sqlalchemy[asyncio] alembic psycopg2-binary python-jose python-multipart
pip freeze > requirements.txt

# Frontend setup
cd ..
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom zustand axios i18next react-i18next
npm install -D tailwindcss postcss autoprefixer @tailwindcss/forms
npx tailwindcss init -p
```

**Day 2: Database**
```bash
# Start PostgreSQL (Docker)
docker run --name communitycircle-db \
  -e POSTGRES_PASSWORD=devpass \
  -e POSTGRES_DB=communitycircle \
  -p 5432:5432 \
  -d postgis/postgis:16-3.4

# Create migrations
cd backend
alembic init alembic
# Copy schema from this document into migration files
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Day 3-4: Authentication**
- Implement user registration (phone + email)
- Phone verification (SMS OTP)
- JWT authentication
- User profile endpoints

**Day 5: Project 1 Backend**
- Posts CRUD API
- Geohash search
- Matching logic

**Weekend: Project 1 Frontend**
- Post list view
- Create post form
- Map view
- Basic styling

---

### 7.2 Essential Resources

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- PostgreSQL + PostGIS: https://postgis.net/
- Fly.io Deployment: https://fly.io/docs/
- Plivo SMS: https://www.plivo.com/docs/sms/

**Code Examples:**
- FastAPI + PostgreSQL: https://github.com/tiangolo/full-stack-fastapi-template
- React PWA: https://github.com/cra-template/pwa
- Zustand: https://github.com/pmndrs/zustand

**Community:**
- r/FastAPI: Reddit community
- React Discord: https://reactcommunity.org/
- Open Source Collective: https://www.oscollective.org/

---

### 7.3 Getting Help

**When Stuck:**
1. Check this document first (likely has answer)
2. Search GitHub issues (existing solutions)
3. Ask in Discord/Slack community
4. Stack Overflow (tag: fastapi, reactjs, postgis)
5. Read official docs (always up-to-date)

**Common Mistakes to Avoid:**
- ❌ Building all 4 projects simultaneously (do sequentially!)
- ❌ Skipping tests ("I'll add them later" = never)
- ❌ Hardcoding secrets (use environment variables)
- ❌ Over-engineering early (KISS principle)
- ❌ Ignoring accessibility (fix early, not later)

---

## Conclusion

You now have a complete blueprint for building an integrated mutual aid platform combining:
- ✅ **Discovery** (Pantry Locator)
- ✅ **Matching** (Needs & Offers Board)
- ✅ **Coordination** (Volunteer Scheduling)
- ✅ **Community** (Pods/Micro-Circles)

**Timeline Summary:**
- **Weeks 1-4:** Project 1 (Needs & Offers) + Core Platform
- **Weeks 5-8:** Project 3 (Volunteer Scheduling)
- **Weeks 9-10:** Project 10 (Pantry Locator)
- **Weeks 11-14:** Project 2 (Pods)
- **Weeks 15-16:** Polish & Launch

**Total: 16 weeks to full MVP**

**Critical Success Factors:**
1. **Start simple** - Build Project 1 first, prove value
2. **Test continuously** - Every feature needs tests
3. **Community feedback** - Beta test with real users early
4. **Accessibility first** - Not an afterthought
5. **Privacy by design** - Bake it into architecture

**You're Ready to Build!**

The research is done. The architecture is designed. The database schema is ready. The timeline is clear.

Now it's time to execute. Start with Week 1, Day 1. Setup your repo. Write your first line of code.

The community needs this. Let's build it together. 🚀

---

**END OF DOCUMENT**

*Questions? Comments? Feedback? Open an issue on GitHub or reach out to the community.*
