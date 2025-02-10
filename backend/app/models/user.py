from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # User-specific settings
    use_openai = Column(Boolean, default=False)
    enable_document_search = Column(Boolean, default=False)
    handle_urls = Column(Boolean, default=False)
    check_db = Column(Boolean, default=False) 