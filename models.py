from sqlalchemy import create_engine, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base
import datetime


Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)


    def __repr__(self):
        return (f"User(telegram_id={self.telegram_id}, username={self.username}, first_name={self.first_name}, "
                f"last_name={self.last_name})")
