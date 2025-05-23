from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import User
from settings import DATABASE_URL


engine = create_engine(DATABASE_URL)


def get_users():
    with Session(engine) as session:
        return session.query(User).limit(10).all()
