import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

CONNECTION_STRING = os.getenv("SQLAZURECONNSTR_swdb")

params = urllib.parse.quote_plus(CONNECTION_STRING)
DATABASE_URL = f"mssql+pyodbc://?odbc_connect={params}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Drop all tables and delete all data
def drop_tables():
    from models import Base
    Base.metadata.drop_all(bind=engine)

def create_tables(drop=False):
    if drop:
        drop_tables()
    from models import Base
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
