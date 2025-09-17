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

## Local Setup and Installation

This project can be run locally without Docker. Follow these steps to set up the environment:

### 1. Install Dependencies

First, install the required system dependencies, including PostgreSQL and PostGIS:

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib postgis
```

### 2. Set Up the Database

Start the PostgreSQL service and create a new database for the application:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres createdb appdb
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

### 3. Install Python Packages

Install the required Python packages using pip:

```bash
pip3 install -r requirements.txt
```

### 4. Run Database Migrations

Create the necessary tables and enable the PostGIS extension by running the following SQL commands:

```bash
sudo -u postgres psql appdb -c "
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE TABLE features (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'queued',
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ,
    geom geography(POINT, 4326) NOT NULL
);
CREATE INDEX idx_features_geom ON features USING GIST (geom);
CREATE TABLE footprints (
    feature_id UUID PRIMARY KEY REFERENCES features(id) ON DELETE CASCADE,
    buffer_m INTEGER NOT NULL,
    area_m2 DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    geom geography(POLYGON, 4326) NOT NULL
);
CREATE INDEX idx_footprints_geom ON footprints USING GIST (geom);
"
```

### 5. Run the Application

Finally, start the FastAPI application using Uvicorn:

```bash
cd app
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/appdb"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Running Tests

### Automated Testing (Recommended)

The project includes comprehensive automated tests that validate the complete workflow:

```bash
# Run smoke tests (validates complete end-to-end workflow)
export API_URL="http://localhost:8000"
python -m pytest tests/test_smoke.py -v

# Run unit tests (validates individual components)
python -m pytest tests/test_unit.py -v
```

**Expected Results:**
```
tests/test_smoke.py::test_health PASSED
tests/test_smoke.py::test_flow PASSED
tests/test_unit.py::test_create_feature_returns_uuid PASSED
tests/test_unit.py::test_get_feature_returns_none_for_nonexistent PASSED
```

### Manual API Testing

You can also test the API manually using various methods:

#### 1. FastAPI Interactive Documentation (Easiest)
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

#### 2. Browser Testing (GET requests only)
- Health check: `http://localhost:8000/healthz`
- Get feature: `http://localhost:8000/features/{uuid}`
- Find nearby: `http://localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=1000`

#### 3. PowerShell Testing (Windows)
```powershell
# Create feature
$body = @{
    name = "Site A"
    lat = 45.5017
    lon = -73.5673
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/features" -Method POST -Body $body -ContentType "application/json"
$featureId = ($response.Content | ConvertFrom-Json).id

# Process feature
Invoke-WebRequest -Uri "http://localhost:8000/features/$featureId/process" -Method POST

# Get feature details
Invoke-WebRequest -Uri "http://localhost:8000/features/$featureId" -Method GET

# Find nearby features
Invoke-WebRequest -Uri "http://localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=1000" -Method GET
```

#### 4. Postman/API Testing Tools
- Import the API endpoints into Postman, Insomnia, or similar tools
- Use the interactive documentation at `/docs` for easy testing

## Docker Setup with pgAdmin (Recommended)

This is the **recommended approach** for testing and development. It provides a complete environment with database inspection capabilities.

### 1. Start All Services

```bash
docker-compose up --build -d
```

This will start:
- **PostgreSQL with PostGIS** on port 5432
- **FastAPI application** on port 8000
- **pgAdmin** on port 5050

### 2. Run Database Migrations

After starting the services, run the database migrations inside the container:

```bash
# Run migrations inside the API container
docker-compose exec api alembic upgrade head
```

### 3. Test the Complete Workflow

#### Option A: Automated Testing (Recommended)
```bash
# Run smoke tests from host machine
export API_URL="http://localhost:8000"
python -m pytest tests/test_smoke.py -v

# Run unit tests
python -m pytest tests/test_unit.py -v
```

#### Option B: Interactive Testing
- **FastAPI Docs**: `http://localhost:8000/docs` (easiest way to test)
- **Health Check**: `http://localhost:8000/healthz`
- **Manual API calls**: Use PowerShell, Postman, or browser

### 4. Inspect Data in pgAdmin

Access the visual database interface to see your spatial data:

1. **Open pgAdmin**: `http://localhost:5050`
2. **Login**:
   - Email: `admin@admin.com`
   - Password: `admin`
3. **Connect to database**:
   - Host: `db`
   - Port: `5432`
   - Database: `appdb`
   - Username: `postgres`
   - Password: `postgres`

4. **Run these queries to validate your data**:

```sql
-- Check PostGIS extension is enabled
SELECT * FROM pg_extension WHERE extname = 'postgis';

-- View all features with their geometries
SELECT id, name, status, ST_AsText(geom) as point_geometry 
FROM features;

-- View processed features with buffer areas
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

### 5. Expected Results

After running the tests and creating features, you should see:
- ✅ **Smoke tests pass**: Complete workflow validation
- ✅ **Unit tests pass**: Component functionality validation
- ✅ **pgAdmin shows spatial data**: PostGIS geometries visible
- ✅ **Buffer areas calculated**: ~785,000 m² for 500m radius
- ✅ **Spatial queries working**: Distance calculations and nearby searches

## Design Decisions and Trade-offs

- **Database Setup**: Instead of relying on Alembic for database migrations, the setup was simplified by creating the tables directly with SQL. This was done to overcome some initial setup issues with Alembic and to keep the project focused on the core application logic.
- **API Routing**: The API routes were reordered to ensure that the `/features/near` endpoint is matched correctly and not mistaken for a dynamic `/features/{feature_id}` route. This is a common consideration in FastAPI to avoid routing conflicts.
- **Error Handling**: The service layer includes basic error handling to ensure that database transactions are rolled back in case of an error during feature processing.

## Future Improvements

- **Alembic Migrations**: For a production environment, it would be beneficial to fully implement Alembic for database schema management to ensure version control and easier updates.
- **Configuration Management**: The database connection details are currently hardcoded in the setup instructions. For a more robust solution, these should be managed through environment variables and a proper configuration file.
- **Asynchronous Processing**: The feature processing is currently synchronous. For a high-volume system, this could be moved to a background task queue (e.g., Celery) to improve API responsiveness.


