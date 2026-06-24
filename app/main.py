from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routes.links import redirect_to_url, router as links_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener")
app.include_router(links_router)

# Registered after /links router so it doesn't shadow /links/*, /docs, or /openapi.json.
app.get("/{code}", tags=["redirect"])(redirect_to_url)
