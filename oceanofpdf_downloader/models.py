from dataclasses import dataclass
from enum import Enum


class BookState(str, Enum):
    NEW = "new"
    SKIPPED = "skipped"
    SCHEDULED = "scheduled"
    DONE = "done"
    RETRY = "retry"


@dataclass
class Book:
    title: str
    detail_url: str
    language: str
    genre: str


@dataclass
class BookRecord:
    id: int
    title: str
    detail_url: str
    language: str
    genre: str
    state: BookState
    created_at: str
    updated_at: str
