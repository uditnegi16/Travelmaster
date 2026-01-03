from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)  # Clerk ID
    stripe_id = Column(String)
    tokens_used = Column(Integer, default=0)
    subscription = Column(String, default='free')
