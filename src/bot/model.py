from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import BaseModel
from pymongo import ASCENDING, IndexModel


class IdProjection(BaseModel):
    id: PydanticObjectId


class User(Document):
    user_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    full_name: str
    language_code: str | None = None
    is_premium: bool | None = None


class Product(Document):
    user_id: int
    url: str
    name: str
    price: str
    min_price: str
    max_price: str
    currency: str
    created_at: datetime
    updated_at: datetime
    checked_at: datetime

    @classmethod
    async def get_all_ids(cls, user_id: int) -> list[str]:
        """Получить все ObjectId пользователя в порядке добавления."""
        products = (
            await cls.find(cls.user_id == user_id).sort('+_id').to_list()
        )
        return [str(product.id) for product in products]

    @classmethod
    async def get_documents_by_ids(
        cls, telegram_id: int, ids: list[str]
    ) -> list["Product"]:
        """Получить документы по списку ObjectId."""
        object_ids = [PydanticObjectId(id_) for id_ in ids]
        products = await cls.find_many(
            {"user_id": telegram_id, "_id": {"$in": object_ids}}
        ).to_list()
        id_map = {str(product.id): product for product in products}
        return [id_map[i] for i in ids if i in id_map]

    class Settings:
        indexes = [
            IndexModel(
                [("user_id", ASCENDING), ("url", ASCENDING)], unique=True
            ),
            IndexModel(
                [("user_id", ASCENDING), ("name", ASCENDING)], unique=True
            ),
        ]
