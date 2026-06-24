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


def get_link_by_code(db: Session, code: str) -> Link | None:
    return db.query(Link).filter(Link.short_code == code).first()


def increment_click_count(db: Session, link: Link) -> None:
    link.click_count += 1
    db.commit()
