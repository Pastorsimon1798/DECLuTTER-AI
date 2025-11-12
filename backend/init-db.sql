-- Initialize database extensions for CommunityCircle

-- Enable PostGIS for geospatial features
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Display installed extensions
\dx
