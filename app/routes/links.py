from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/links", tags=["links"])


@router.post("", response_model=schemas.LinkResponse, status_code=201)
def create_link(body: schemas.LinkCreate, db: Session = Depends(get_db)) -> schemas.LinkResponse:
    link = crud.create_link(db, str(body.url))
    return link
