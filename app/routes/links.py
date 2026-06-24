from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=schemas.LinkResponse, status_code=201)
def create_link(body: schemas.LinkCreate, db: Session = Depends(get_db)) -> schemas.LinkResponse:
    link = crud.create_link(db, str(body.url))
    return link


@router.get("", response_model=schemas.LinkList)
def list_links(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> schemas.LinkList:
    items, total = crud.list_links(db, limit, offset)
    return schemas.LinkList(items=items, total=total)


@router.get("/{code}/stats", response_model=schemas.LinkStats)
def get_link_stats(code: str, db: Session = Depends(get_db)) -> schemas.LinkStats:
    link = crud.get_link_by_code(db, code)
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    return link


def redirect_to_url(code: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """Registered on the main app (not this router) to live at /{code}."""
    link = crud.get_link_by_code(db, code)
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    crud.increment_click_count(db, link)
    return RedirectResponse(url=link.original_url, status_code=307)
