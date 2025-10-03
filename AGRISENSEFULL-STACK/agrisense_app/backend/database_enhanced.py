"""
Enhanced database configuration with PostgreSQL, Redis, and async support
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

# SQLAlchemy async imports
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker  # type: ignore
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # type: ignore
    from sqlalchemy import String, Float, DateTime, Integer, Text, Boolean, JSON  # type: ignore
    from sqlalchemy.sql import func  # type: ignore
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Comprehensive fallback types for when SQLAlchemy is not available
    class DeclarativeBase:  # type: ignore
        def __init_subclass__(cls, **kwargs):
            pass
    
    class Mapped:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def __class_getitem__(cls, item):
            return cls
    
    def mapped_column(*args, **kwargs):  # type: ignore
        return None
    
    def create_async_engine(*args, **kwargs):  # type: ignore
        return None
    
    def async_sessionmaker(*args, **kwargs):  # type: ignore
        return None
    
    AsyncSession = String = Float = DateTime = Integer = Text = Boolean = JSON = None
    
    class Mapped:
        def __init__(self, type_=None):
            self.type_ = type_
        
        def __class_getitem__(cls, item):
            return cls(item)
    
    def mapped_column(*args, **kwargs):
        return None
    
    class MockFunc:
        def now(self):
            return "NOW()"
        
        def __getattr__(self, name):
            return lambda *args, **kwargs: f"{name.upper()}()"
    
    func = MockFunc()
    
    # Mock column types that accept arguments
    class MockColumnType:
        def __init__(self, *args, **kwargs):
            pass
        
        def __call__(self, *args, **kwargs):
            return self
    
    String = Float = DateTime = Integer = Text = Boolean = JSON = MockColumnType

# Redis imports
try:
    import redis.asyncio as redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Mock redis module
    class MockRedis:  # type: ignore
        @staticmethod
        def from_url(*args, **kwargs):
            return MockRedisClient()
    
    class MockRedisClient:
        async def ping(self): pass
        async def get(self, key): return None
        async def setex(self, key, ttl, value): return True
        async def delete(self, *keys): return len(keys)
        async def exists(self, key): return False
        async def keys(self, pattern): return []
        async def close(self): pass
        def pipeline(self): return self
    
    redis = MockRedis()

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://agrisense:agrisense@localhost:5432/agrisense")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

logger = logging.getLogger(__name__)


# Database Models
if SQLALCHEMY_AVAILABLE:
    class Base(DeclarativeBase):  # type: ignore
        pass
else:
    class Base:  # type: ignore
        __tablename__ = ""
        pass


if SQLALCHEMY_AVAILABLE:
    class SensorReading(Base):  # type: ignore
        __tablename__ = "sensor_readings"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
        zone_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # type: ignore
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)  # type: ignore
        temperature_c: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        humidity_pct: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        soil_moisture_pct: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        ph: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        ec_ds_m: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        light_lux: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        raw_data: Mapped[Optional[dict]] = mapped_column(JSON)  # type: ignore
else:
    class SensorReading:
        __tablename__ = "sensor_readings"


if SQLALCHEMY_AVAILABLE:
    class Recommendation(Base):  # type: ignore
        __tablename__ = "recommendations"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
        zone_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # type: ignore
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)  # type: ignore
        water_liters: Mapped[float] = mapped_column(Float, nullable=False)  # type: ignore
        fert_n_g: Mapped[float] = mapped_column(Float, default=0.0)  # type: ignore
        fert_p_g: Mapped[float] = mapped_column(Float, default=0.0)  # type: ignore
        fert_k_g: Mapped[float] = mapped_column(Float, default=0.0)  # type: ignore
        confidence_score: Mapped[float] = mapped_column(Float, default=0.0)  # type: ignore
        model_version: Mapped[str] = mapped_column(String(50))  # type: ignore
        expected_savings_liters: Mapped[float] = mapped_column(Float, default=0.0)  # type: ignore
        tips: Mapped[Optional[str]] = mapped_column(Text)  # type: ignore
        extra_data: Mapped[Optional[dict]] = mapped_column(JSON)  # type: ignore

    class Alert(Base):  # type: ignore
        __tablename__ = "alerts"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
        zone_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # type: ignore
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)  # type: ignore
        alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # type: ignore
        severity: Mapped[str] = mapped_column(String(20), nullable=False)  # type: ignore
        title: Mapped[str] = mapped_column(String(200), nullable=False)  # type: ignore
        message: Mapped[str] = mapped_column(Text, nullable=False)  # type: ignore
        acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)  # type: ignore
        acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # type: ignore
        resolved: Mapped[bool] = mapped_column(Boolean, default=False)  # type: ignore
        resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))  # type: ignore
        extra_data: Mapped[Optional[dict]] = mapped_column(JSON)  # type: ignore

    class TankLevel(Base):  # type: ignore
        __tablename__ = "tank_levels"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
        tank_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # type: ignore
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)  # type: ignore
        level_liters: Mapped[float] = mapped_column(Float, nullable=False)  # type: ignore
        capacity_liters: Mapped[float] = mapped_column(Float, nullable=False)  # type: ignore
        percentage: Mapped[float] = mapped_column(Float, nullable=False)  # type: ignore
        temperature_c: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        quality_score: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore

    class WeatherData(Base):  # type: ignore
        __tablename__ = "weather_data"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)  # type: ignore
        location: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # type: ignore
        timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)  # type: ignore
        temperature_c: Mapped[float] = mapped_column(Float, nullable=False)  # type: ignore
        humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)  # type: ignore
        pressure_mb: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        wind_speed_ms: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        wind_direction_deg: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore
        precipitation_mm: Mapped[Optional[float]] = mapped_column(Float)  # type: ignore

    from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
    from sqlalchemy.orm import Mapped, mapped_column  # type: ignore
    from fastapi_users.models import UP, ID, UserProtocol

    class User(Base, SQLAlchemyBaseUserTableUUID):  # type: ignore
        __tablename__ = "users"
        first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # type: ignore
        last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # type: ignore
        role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)  # type: ignore
else:
    # Mock model classes when SQLAlchemy not available
    class Recommendation:  # type: ignore
        __tablename__ = "recommendations"

    class Alert:  # type: ignore
        __tablename__ = "alerts"

    class TankLevel:  # type: ignore
        __tablename__ = "tank_levels"

    class WeatherData:  # type: ignore
        __tablename__ = "weather_data"

    class User:  # type: ignore
        __tablename__ = "users"


# Database Manager Class
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)  # type: ignore


# Database Manager Class
class DatabaseManager:
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        if SQLALCHEMY_AVAILABLE:
            self.engine = None
            self.session_factory = None
        else:
            # Mock implementations when SQLAlchemy not available
            self.engine = None  # Will be a mock engine
            self.session_factory = None  # Will be a mock session factory

    async def initialize(self):
        """Initialize database connection and create tables"""
        if not SQLALCHEMY_AVAILABLE:
            logger.warning("SQLAlchemy not available, database features disabled")
            return
            
        self.engine = create_async_engine(
            self.database_url,
            echo=os.getenv("SQL_DEBUG", "0") == "1",
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

        # Create tables
        try:
            if self.engine is not None and hasattr(Base, 'metadata'):
                async with self.engine.begin() as conn:  # type: ignore
                    await conn.run_sync(Base.metadata.create_all)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")

    async def close(self):
        """Close database connections"""
        if not SQLALCHEMY_AVAILABLE or not self.engine:
            return
            
        try:
            await self.engine.dispose()  # type: ignore
        except Exception as e:
            logger.error(f"Error closing database: {e}")

    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        if not SQLALCHEMY_AVAILABLE:
            # Return a mock session context
            class MockSession:
                async def __aenter__(self):
                    return self
                    
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
                    
                async def commit(self): 
                    pass
                    
                async def rollback(self): 
                    pass
                    
                async def close(self): 
                    pass
                    
                async def execute(self, query, *args, **kwargs):
                    """Mock execute method"""
                    class MockResult:
                        def scalar_one_or_none(self):
                            return None
                        def scalars(self):
                            class MockScalars:
                                def all(self):
                                    return []
                                def first(self):
                                    return None
                            return MockScalars()
                        def mappings(self):
                            class MockMappings:
                                def all(self):
                                    return []
                                def first(self):
                                    return None
                            return MockMappings()
                        def fetchone(self):
                            return None
                        def fetchall(self):
                            return []
                    return MockResult()
                    
            yield MockSession()
            return
            
        if not self.session_factory:
            await self.initialize()

        if not self.session_factory:
            yield None
            return

        async with self.session_factory() as session:  # type: ignore
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Redis Cache Manager
class CacheManager:
    def __init__(self, redis_url: str = REDIS_URL):
        self.redis_url = redis_url
        if REDIS_AVAILABLE:
            self.redis_client = None
        else:
            self.redis_client = MockRedisClient()

    async def initialize(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using mock cache")
            self.redis_client = MockRedisClient()
            return
            
        self.redis_client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True, max_connections=20)

        # Test connection
        await self.redis_client.ping()

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            await self.initialize()

        if not self.redis_client:
            return None

        value = await self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self.redis_client:
            await self.initialize()

        if not self.redis_client:
            return False

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        return await self.redis_client.setex(key, ttl, value)

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            await self.initialize()

        if not self.redis_client:
            return False

        return bool(await self.redis_client.delete(key))

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            await self.initialize()

        if not self.redis_client:
            return False

        return bool(await self.redis_client.exists(key))

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.redis_client:
            await self.initialize()

        if not self.redis_client:
            return 0

        keys = await self.redis_client.keys(pattern)
        if keys:
            return await self.redis_client.delete(*keys)
        return 0


# Global instances
db_manager = DatabaseManager()
cache_manager = CacheManager()


# Dependency functions for FastAPI
async def get_db_session():
    """FastAPI dependency for database session"""
    async with db_manager.get_session() as session:
        yield session


async def get_cache():
    """FastAPI dependency for cache manager"""
    if not cache_manager.redis_client:
        await cache_manager.initialize()
    return cache_manager


# Utility functions
async def cache_sensor_reading(reading: Dict[str, Any], ttl: int = 300) -> None:
    """Cache latest sensor reading"""
    zone_id = reading.get("zone_id", "default")
    cache_key = f"sensor:latest:{zone_id}"
    await cache_manager.set(cache_key, reading, ttl)


async def get_cached_sensor_reading(zone_id: str) -> Optional[Dict[str, Any]]:
    """Get cached sensor reading"""
    cache_key = f"sensor:latest:{zone_id}"
    return await cache_manager.get(cache_key)


async def cache_recommendation(zone_id: str, recommendation: Dict[str, Any], ttl: int = 1800) -> None:
    """Cache recommendation"""
    cache_key = f"recommendation:latest:{zone_id}"
    await cache_manager.set(cache_key, recommendation, ttl)


async def get_cached_recommendation(zone_id: str) -> Optional[Dict[str, Any]]:
    """Get cached recommendation"""
    cache_key = f"recommendation:latest:{zone_id}"
    return await cache_manager.get(cache_key)


async def cache_weather_data(location: str, weather_data: Dict[str, Any], ttl: int = 3600) -> None:
    """Cache weather data"""
    cache_key = f"weather:{location}"
    await cache_manager.set(cache_key, weather_data, ttl)


async def get_cached_weather_data(location: str) -> Optional[Dict[str, Any]]:
    """Get cached weather data"""
    cache_key = f"weather:{location}"
    return await cache_manager.get(cache_key)


# Health check function
async def check_db_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        start_time = datetime.utcnow()
        async with db_manager.get_session() as session:
            result = await session.execute("SELECT 1")  # type: ignore
            result.fetchone()

        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000

        return {"status": "healthy", "response_time_ms": response_time, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}


async def check_cache_health() -> Dict[str, Any]:
    """Check Redis cache connectivity and performance"""
    try:
        start_time = datetime.utcnow()
        if not cache_manager.redis_client:
            await cache_manager.initialize()

        if cache_manager.redis_client:
            await cache_manager.redis_client.ping()
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000

        return {"status": "healthy", "response_time_ms": response_time, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}


async def initialize_database() -> None:
    """Initialize database and create tables if needed"""
    try:
        await db_manager.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def cleanup_database() -> None:
    """Cleanup database connections"""
    try:
        await db_manager.close()
        await cache_manager.close()
        logger.info("Database cleanup completed")
    except Exception as e:
        logger.error(f"Failed to cleanup database: {e}")


async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health - alias for check_cache_health"""
    return await check_cache_health()


async def get_async_session():
    """Get async database session"""
    return db_manager.get_session()
