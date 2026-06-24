from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.models import Base
from app.routes.auth import router as auth_router
from app.routes.links import redirect_to_url, router as links_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Link Shortener")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router)
app.include_router(links_router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


# Registered after /links router so it doesn't shadow /links/*, /docs, or /openapi.json.
app.get("/{code}", tags=["redirect"])(redirect_to_url)
