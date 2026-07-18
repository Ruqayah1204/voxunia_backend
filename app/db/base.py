"""This file contains the base configuration for the database models in the application.
    The declarative_base is used to create the base class for all models, and all models should inherit from this base class.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

# import all models here
from app.models import user, attendee, group, session, question, vote, comment