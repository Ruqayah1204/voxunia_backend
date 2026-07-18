"""This file contains the sqlalchemy session configuration for the application.
It connects to the database using the settings defined in the config.py file and provides a 
sessionmaker for creating database sessions.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    # Inject dependency function to get a database session for each request
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()
