from datetime import datetime
from pydantic import BaseModel


class BaseScheme(BaseModel):
    """Base scheme for goods."""

    telegram_id: int
    url: str
    name: str
    price: str | None = None
    min_price: str | None = None
    max_price: str | None = None
    created_at: datetime
    created_at: datetime
