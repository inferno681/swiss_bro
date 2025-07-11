from datetime import datetime

from pydantic import BaseModel


class BaseScheme(BaseModel):
    """Base scheme for goods."""

    telegram_id: int
    url: str
    name: str
    price: str
    min_price: str | None = None
    max_price: str | None = None
    currency: str
    created_at: datetime
    updated_at: datetime
