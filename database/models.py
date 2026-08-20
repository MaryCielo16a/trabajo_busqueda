from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import DB_PATH

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    salary = Column(String)
    description = Column(Text)
    url = Column(String, unique=True, nullable=False)
    source = Column(String)  # 'computrabajo', 'bumeran', 'linkedin'
    posted_date = Column(DateTime)
    scraped_date = Column(DateTime, default=datetime.now)
    is_remote = Column(Boolean, default=False)
    required_experience = Column(String)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    job_id = Column(String, nullable=False)
    applied_date = Column(DateTime, default=datetime.now)
    status = Column(String, default="pending")  # pending, applied, rejected, accepted
    notes = Column(Text)

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(String)

def init_db():
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session()
