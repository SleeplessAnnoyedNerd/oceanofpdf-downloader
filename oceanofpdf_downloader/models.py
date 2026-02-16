from dataclasses import dataclass


@dataclass
class Book:
    title: str
    detail_url: str
    language: str
    genre: str
