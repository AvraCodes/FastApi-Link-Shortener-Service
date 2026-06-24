from datetime import datetime

from pydantic import BaseModel, HttpUrl


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class LinkCreate(BaseModel):
    url: HttpUrl


class LinkResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkStats(LinkResponse):
    click_count: int


class LinkList(BaseModel):
    items: list[LinkResponse]
    total: int
