# PostGIS service layer implementation
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
from datetime import datetime, timezone

def now():
    return datetime.now(timezone.utc)

def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    """Insert a new feature with a point geometry."""
    feature_id = uuid.uuid4()
    current_time = now()
    
    query = text("""
        INSERT INTO features (id, name, status, attempts, created_at, updated_at, geom)
        VALUES (:id, :name, 'queued', 0, :created_at, :updated_at, 
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)
    """)
    
    db.execute(query, {
        'id': feature_id,
        'name': name,
        'lon': lon,
        'lat': lat,
        'created_at': current_time,
        'updated_at': current_time
    })
    db.commit()
    return feature_id

def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    """Create a 500m buffer around the feature point, calculate area, and update status."""
    try:
        # Check if feature exists
        check_query = text("SELECT id FROM features WHERE id = :feature_id")
        result = db.execute(check_query, {'feature_id': feature_id}).fetchone()
        if not result:
            return False
        
        current_time = now()
        
        # Create buffer and calculate area, then insert into footprints
        buffer_query = text("""
            INSERT INTO footprints (feature_id, buffer_m, area_m2, created_at, geom)
            SELECT 
                :feature_id,
                :buffer_m,
                ST_Area(ST_Buffer(f.geom, :buffer_m)),
                :created_at,
                ST_Buffer(f.geom, :buffer_m)
            FROM features f
            WHERE f.id = :feature_id
        """)
        
        db.execute(buffer_query, {
            'feature_id': feature_id,
            'buffer_m': buffer_m,
            'created_at': current_time
        })
        
        # Update feature status to 'done'
        update_query = text("""
            UPDATE features 
            SET status = 'done', updated_at = :updated_at, attempts = attempts + 1
            WHERE id = :feature_id
        """)
        
        db.execute(update_query, {
            'feature_id': feature_id,
            'updated_at': current_time
        })
        
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"Error processing feature {feature_id}: {e}")
        return False

def get_feature(db: Session, feature_id: str):
    """Get feature details including buffer area if available."""
    query = text("""
        SELECT 
            f.id,
            f.name,
            f.status,
            f.attempts,
            f.created_at,
            f.updated_at,
            fp.buffer_m,
            fp.area_m2 as buffer_area_m2
        FROM features f
        LEFT JOIN footprints fp ON f.id = fp.feature_id
        WHERE f.id = :feature_id
    """)
    
    result = db.execute(query, {'feature_id': feature_id}).fetchone()
    if not result:
        return None
    
    return {
        'id': str(result.id),
        'name': result.name,
        'status': result.status,
        'attempts': result.attempts,
        'created_at': result.created_at.isoformat() if result.created_at else None,
        'updated_at': result.updated_at.isoformat() if result.updated_at else None,
        'buffer_m': result.buffer_m,
        'buffer_area_m2': result.buffer_area_m2
    }

def features_near(db: Session, lat: float, lon: float, radius_m: int):
    """Find features within radius using ST_DWithin, ordered by distance."""
    query = text("""
        SELECT 
            f.id,
            f.name,
            f.status,
            f.attempts,
            f.created_at,
            f.updated_at,
            fp.buffer_m,
            fp.area_m2 as buffer_area_m2,
            ST_Distance(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography) as distance_m
        FROM features f
        LEFT JOIN footprints fp ON f.id = fp.feature_id
        WHERE ST_DWithin(f.geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius_m)
        ORDER BY distance_m
    """)
    
    results = db.execute(query, {
        'lat': lat,
        'lon': lon,
        'radius_m': radius_m
    }).fetchall()
    
    features = []
    for result in results:
        features.append({
            'id': str(result.id),
            'name': result.name,
            'status': result.status,
            'attempts': result.attempts,
            'created_at': result.created_at.isoformat() if result.created_at else None,
            'updated_at': result.updated_at.isoformat() if result.updated_at else None,
            'buffer_m': result.buffer_m,
            'buffer_area_m2': result.buffer_area_m2,
            'distance_m': float(result.distance_m) if result.distance_m else None
        })
    
    return features

