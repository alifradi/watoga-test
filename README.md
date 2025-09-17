# Geo Ingestion Service (FastAPI + PostGIS)

This project is a FastAPI-based service for ingesting and querying geospatial data using PostGIS. It provides a simple API for creating, processing, and retrieving geographic features.

## 🚀 Quick Start (Docker - Recommended)

```bash
# 1. Start all services
docker-compose up --build -d

# 2. Run database migrations
docker-compose exec api alembic upgrade head

# 3. Test the API
# Option A: Interactive docs (easiest)
# Open http://localhost:8000/docs in your browser

# Option B: Automated tests
export API_URL="http://localhost:8000"
python -m pytest tests/test_smoke.py -v

# 4. Inspect data visually
# Open http://localhost:5050 (pgAdmin)
# Login: admin@admin.com / admin
# Connect to: db:5432 / postgres / postgres / appdb
```

## Features

- **Create Features**: `POST /features` to create a new feature with a name and geographic coordinates (latitude and longitude).
- **Process Features**: `POST /features/{id}/process` to generate a 500-meter buffer around a feature, calculate its area, and store it as a polygon.
- **Get Feature Details**: `GET /features/{id}` to retrieve the status and buffer area of a specific feature.
- **Find Nearby Features**: `GET /features/near` to find all features within a given radius of a specific point.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for running tests from host machine)

## Step-by-Step Testing Guide

### Step 1: Start Services and Run Migrations

```bash
# Start all services
docker-compose up --build -d

# Run database migrations
docker-compose exec api alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_init, TODO migration — enable PostGIS and create geography columns
```

**Database Preview:** PostGIS extension enabled, `features` and `footprints` tables created with geography columns and GIST indexes.

### Step 2: Interactive API Testing (Swagger UI)

Open `http://localhost:8000/docs` in your browser to access the interactive API documentation.

#### API Endpoints Testing Table

| Endpoint | Method | Input | Expected Output | Database Impact |
|----------|--------|-------|-----------------|-----------------|
| **Health Check** | GET | None | `{"status":"ok"}` | None |
| **Readiness Check** | GET | None | `{"status":"ready"}` | None |
| **Create Feature** | POST | `{"name":"Site A","lat":45.5017,"lon":-73.5673}` | `{"id":"uuid-here"}` | New row in `features` table with POINT geometry |
| **Process Feature** | POST | `{feature_id}` (from create) | `{"processed":true}` | New row in `footprints` table with POLYGON buffer, status updated to "done" |
| **Get Feature** | GET | `{feature_id}` | `{"id":"uuid","name":"Site A","status":"done","buffer_m":500,"buffer_area_m2":785398.16}` | None (read-only) |
| **Find Nearby** | GET | `lat=45.5017&lon=-73.5673&radius_m=1000` | `[{"id":"uuid","name":"Site A","status":"done","distance_m":0.0}]` | None (read-only) |

#### Testing Workflow in Swagger UI

1. **Test Health Endpoints**
   - Click on `GET /healthz` → Try it out → Execute
   - Click on `GET /readyz` → Try it out → Execute

2. **Create a Feature**
   - Click on `POST /features` → Try it out
   - Enter: `{"name":"Site A","lat":45.5017,"lon":-73.5673}`
   - Click Execute
   - **Copy the returned UUID** for next steps

3. **Process the Feature**
   - Click on `POST /features/{feature_id}/process` → Try it out
   - Paste the UUID from step 2
   - Click Execute

4. **Get Feature Details**
   - Click on `GET /features/{feature_id}` → Try it out
   - Paste the same UUID
   - Click Execute
   - **Verify**: status="done", buffer_area_m2≈785000

5. **Find Nearby Features**
   - Click on `GET /features/near` → Try it out
   - Enter: lat=45.5017, lon=-73.5673, radius_m=1000
   - Click Execute
   - **Verify**: Returns your feature with distance_m=0.0

### Step 3: Automated Testing

```bash
# Run smoke tests
export API_URL="http://localhost:8000"
python -m pytest tests/test_smoke.py -v

# Run unit tests
python -m pytest tests/test_unit.py -v
```

**Expected Output:**
```
tests/test_smoke.py::test_health PASSED
tests/test_smoke.py::test_flow PASSED
tests/test_unit.py::test_create_feature_returns_uuid PASSED
tests/test_unit.py::test_get_feature_returns_none_for_nonexistent PASSED
```

### Step 4: Database Inspection with pgAdmin

#### Access pgAdmin
1. **Open**: `http://localhost:5050`
2. **Login**: `admin@admin.com` / `admin`
3. **Connect to database**:
   - Host: `db`
   - Port: `5432`
   - Database: `appdb`
   - Username: `postgres`
   - Password: `postgres`

#### Database State After Each Step

**After Step 1 (Migrations):**
```sql
-- Check PostGIS extension
SELECT * FROM pg_extension WHERE extname = 'postgis';
```
**Expected:** Shows PostGIS extension installed

**After Step 2.3 (Create Feature):**
```sql
-- View created features
SELECT id, name, status, ST_AsText(geom) as point_geometry 
FROM features;
```
**Expected:** One row with status="queued", geometry="POINT(-73.5673 45.5017)"

**After Step 2.4 (Process Feature):**
```sql
-- View processed features with buffers
SELECT f.name, f.status, fp.buffer_m, fp.area_m2, 
       ST_AsText(f.geom) as point_geometry,
       ST_AsText(fp.geom) as buffer_geometry
FROM features f 
JOIN footprints fp ON f.id = fp.feature_id;
```
**Expected:** 
- status="done"
- buffer_m=500
- area_m2≈785000
- point_geometry="POINT(-73.5673 45.5017)"
- buffer_geometry="POLYGON(...)" (complex polygon)

**After Step 2.5 (Find Nearby):**
```sql
-- Test spatial query
SELECT f.name, 
       ST_Distance(f.geom, ST_SetSRID(ST_MakePoint(-73.5673, 45.5017), 4326)::geography) as distance_m
FROM features f
WHERE ST_DWithin(f.geom, ST_SetSRID(ST_MakePoint(-73.5673, 45.5017), 4326)::geography, 1000);
```
**Expected:** Returns your feature with distance_m=0.0

#### Complete Validation Query
```sql
-- Full validation of PostGIS functionality
SELECT 
    'PostGIS Extension' as check_type,
    CASE WHEN EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis') 
         THEN '✅ Enabled' ELSE '❌ Missing' END as status
UNION ALL
SELECT 
    'Features Table',
    CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'features') 
         THEN '✅ Exists' ELSE '❌ Missing' END
UNION ALL
SELECT 
    'Footprints Table',
    CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'footprints') 
         THEN '✅ Exists' ELSE '❌ Missing' END
UNION ALL
SELECT 
    'GIST Indexes',
    CASE WHEN EXISTS(SELECT 1 FROM pg_indexes WHERE tablename IN ('features', 'footprints') AND indexdef LIKE '%GIST%') 
         THEN '✅ Created' ELSE '❌ Missing' END
UNION ALL
SELECT 
    'Processed Features',
    CASE WHEN EXISTS(SELECT 1 FROM features f JOIN footprints fp ON f.id = fp.feature_id) 
         THEN '✅ Data Available' ELSE '❌ No Data' END;
```

## Architecture

- **Database**: PostgreSQL with PostGIS extension for spatial operations
- **API**: FastAPI with automatic OpenAPI documentation
- **Migrations**: Alembic for database schema management
- **Testing**: Comprehensive test suite with smoke tests and unit tests
- **Deployment**: Docker Compose for easy local development and testing

## Key Features Implemented

- ✅ **PostGIS Integration**: All spatial functions working correctly
- ✅ **Complete API**: All user stories implemented and tested
- ✅ **Database Migrations**: Alembic migrations with PostGIS setup
- ✅ **Comprehensive Testing**: Automated tests validating full workflow
- ✅ **Visual Inspection**: pgAdmin interface for database inspection
- ✅ **Docker Deployment**: Easy setup and testing environment


