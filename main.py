from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.db import Base, engine
from api.routers import articles

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(articles.router)

@app.get("/")
def health_check():
  return "Health check complete"