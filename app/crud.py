from sqlalchemy.orm import Session

from app.models import Link, User
from app.shortcode import generate_short_code


def create_user(db: Session, username: str, hashed_password: str) -> User:
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


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


def list_links(db: Session, limit: int, offset: int) -> tuple[list[Link], int]:
    total = db.query(Link).count()
    items = db.query(Link).order_by(Link.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def get_all_links(db: Session) -> list[Link]:
    return db.query(Link).order_by(Link.created_at.desc()).all()
