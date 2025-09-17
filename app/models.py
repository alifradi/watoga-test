from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from geoalchemy2 import Geography
from datetime import datetime, timezone
import uuid
from db import Base

def now():
    return datetime.now(timezone.utc)

class Feature(Base):
    __tablename__ = "features"
    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now, nullable=True)
    geom = mapped_column(Geography(geometry_type='POINT', srid=4326), nullable=False)

class Footprint(Base):
    __tablename__ = "footprints"
    feature_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("features.id", ondelete="CASCADE"), primary_key=True)
    buffer_m: Mapped[int] = mapped_column(Integer, nullable=False)
    area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, nullable=False)
    geom = mapped_column(Geography(geometry_type='POLYGON', srid=4326), nullable=False)
