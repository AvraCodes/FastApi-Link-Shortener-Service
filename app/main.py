from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routes.links import router as links_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener")
app.include_router(links_router)
