from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends
from dotenv import load_dotenv
import os

from .db import session_local

load_dotenv()

SECRET_KEY = os.getenv('AUTH_SECRET_KEY')
ALGORITHM = os.getenv('AUTH_ALGORITHM')

def get_db():
  db = session_local()
  try:
    yield db
  finally:
    db.close()

db_dependency = Annotated[Session, Depends(get_db)]