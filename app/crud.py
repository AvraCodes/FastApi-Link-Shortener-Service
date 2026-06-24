from sqlalchemy.orm import Session

from app.models import Link
from app.shortcode import generate_short_code


def create_link(db: Session, original_url: str) -> Link:
    while True:
        code = generate_short_code()
        if not db.query(Link).filter(Link.short_code == code).first():
            break

    link = Link(short_code=code, original_url=original_url)
    db.add(link)
    db.commit()
    db.refresh(link)
    return link
