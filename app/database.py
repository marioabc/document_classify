from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    document_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    extracted_text = Column(Text, nullable=True)
    extracted_dates = Column(JSON, nullable=True)
    keywords_found = Column(JSON, nullable=True)
    doc_metadata = Column(JSON, nullable=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
