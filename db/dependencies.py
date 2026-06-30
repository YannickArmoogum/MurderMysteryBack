"""FastAPI dependencies for database access."""
from typing import Iterator

import anthropic
from fastapi import Request
from sqlalchemy.orm import Session

from core.config.config import ANTHROPIC_API_KEY

_client: anthropic.Anthropic | None = None

def get_session(request:Request) -> Iterator[Session]:
    db = request.app.state.db #Leaves in db state lifespan
    session = db.get_session()
    try:
        yield session #Return session to be injected
    finally:
        session.close()

def get_anthropic_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client