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

## Validation Testing

After setting up the services, use this table to validate all components are working correctly:

| Component | Command | Expected Result |
|-----------|---------|----------------|
| **Health Check** | `Invoke-WebRequest -Uri "http://localhost:8000/healthz" -Method GET` | `{"status":"ok"}` |
| **Readiness Check** | `Invoke-WebRequest -Uri "http://localhost:8000/readyz" -Method GET` | `{"status":"ready"}` |
| **Create Feature** | `$body = @{"name"="Site A";"lat"=45.5017;"lon"=-73.5673} \| ConvertTo-Json`<br>`Invoke-WebRequest -Uri "http://localhost:8000/features" -Method POST -Body $body -ContentType "application/json"` | `{"id":"uuid-here"}` |
| **Process Feature** | `Invoke-WebRequest -Uri "http://localhost:8000/features/{uuid}/process" -Method POST` | `{"processed":true}` |
| **Get Feature** | `Invoke-WebRequest -Uri "http://localhost:8000/features/{uuid}" -Method GET` | Status: "done", buffer_area_m2: ~785000 |
| **Find Nearby** | `Invoke-WebRequest -Uri "http://localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=1000" -Method GET` | Array with feature data, distance_m: 0.0 |
| **Smoke Tests** | `export API_URL="http://localhost:8000"`<br>`python -m pytest tests/test_smoke.py -v` | `test_health PASSED`<br>`test_flow PASSED` |
| **Unit Tests** | `python -m pytest tests/test_unit.py -v` | `test_create_feature_returns_uuid PASSED`<br>`test_get_feature_returns_none_for_nonexistent PASSED` |

### Interactive API Testing

**FastAPI Documentation**: `http://localhost:8000/docs`
- Provides interactive interface to test all endpoints
- No command line required
- Shows request/response examples

## Database Inspection with pgAdmin

### Access pgAdmin
1. **Open**: `http://localhost:5050`
2. **Login**: `admin@admin.com` / `admin`
3. **Connect to database**:
   - Host: `db`
   - Port: `5432`
   - Database: `appdb`
   - Username: `postgres`
   - Password: `postgres`

### Validation Queries
Run these SQL queries to verify PostGIS functionality:

```sql
-- Check PostGIS extension
SELECT * FROM pg_extension WHERE extname = 'postgis';

-- View processed features with spatial data
SELECT f.name, f.status, fp.buffer_m, fp.area_m2, 
       ST_AsText(f.geom) as point_geometry,
       ST_AsText(fp.geom) as buffer_geometry
FROM features f 
JOIN footprints fp ON f.id = fp.feature_id;

-- Test spatial queries
SELECT f.name, 
       ST_Distance(f.geom, ST_SetSRID(ST_MakePoint(-73.5673, 45.5017), 4326)::geography) as distance_m
FROM features f
WHERE ST_DWithin(f.geom, ST_SetSRID(ST_MakePoint(-73.5673, 45.5017), 4326)::geography, 1000);
```

**Expected Results:**
- PostGIS extension enabled
- Features with point geometries (POINT format)
- Footprints with polygon geometries (POLYGON format)
- Buffer areas ~785,000 m² for 500m radius
- Spatial queries returning distance calculations

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


