"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create sync database URL
sync_database_url = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "sqlite:///") if "sqlite" in settings.DATABASE_URL else settings.DATABASE_URL

# Sync database (for compatibility)
engine = create_engine(
    sync_database_url,
    connect_args={"check_same_thread": False} if "sqlite" in sync_database_url else {},
    echo=False  # Set to True for SQL query logging
)

# Async database engine
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False
)

# Create sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Create base class
Base = declarative_base()

# Sync database dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

# Async database dependency
async def get_async_db() -> Generator[AsyncSession, None, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


def init_db() -> None:
    """
    Initialize database tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise