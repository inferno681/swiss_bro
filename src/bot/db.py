from bson import ObjectId
from pymongo import AsyncMongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

from config import config


class MongoDB:
    """MongoDB client for the bot."""

    def __init__(
        self, client: AsyncMongoClient, db: str, collection: str
    ) -> None:
        self.client = client
        self.db = self.client[db]
        self.collection = self.db[collection]

    async def start_up(self) -> None:
        """Initialize the MongoDB connection."""
        await self.client.aconnect()
        await self.migrate()

    async def close(self) -> None:
        """Close the MongoDB connection."""
        await self.client.aclose()

    async def migrate(self) -> None:
        """Make migration."""
        await self.collection.create_index(
            [('url', 1), ('telegram_id', 1)], unique=True
        )
        await self.collection.create_index(
            [('name', 1), ('telegram_id', 1)], unique=True
        )

    async def get_document(self, **kwargs) -> dict | None:
        """Get a document by URL."""
        return await self.collection.find_one(kwargs)

    async def insert_document(self, document: dict) -> bool:
        """Insert a new document."""
        try:
            await self.collection.insert_one(document)
        except DuplicateKeyError:
            return False
        return True

    async def update_document(self, url: str, update: dict) -> dict | None:
        """Update an existing document by URL."""
        return await self.collection.find_one_and_update(
            {'url': url},
            {'$set': update},
            return_document=ReturnDocument.AFTER,
        )

    async def get_all_documents(
        self, telegram_id: int | None = None
    ) -> list[dict]:
        """Get all documents from the collection."""
        documents = []
        if telegram_id:
            cursor = self.collection.find({'telegram_id': telegram_id})
        else:
            cursor = self.collection.find({})
        async for doc in cursor:
            documents.append(doc)
        return documents

    async def get_documents_by_ids(
        self, telegram_id: int, ids: list[str]
    ) -> list[dict]:
        """Получить документы по списку ObjectId."""
        object_ids = [ObjectId(id_) for id_ in ids]
        cursor = self.collection.find(
            {'_id': {'$in': object_ids}, 'telegram_id': telegram_id}
        )
        return [doc async for doc in cursor]

    async def get_all_ids(self, telegram_id: int) -> list[str]:
        """Получить все ObjectId пользователя в порядке добавления."""
        cursor = self.collection.find({'telegram_id': telegram_id}).sort(
            '_id', 1
        )
        return [str(doc['_id']) async for doc in cursor]

    async def delete_document(self, telegram_id: int, name: str) -> None:
        """Delete a document by name."""
        await self.collection.delete_one(
            {'telegram_id': telegram_id, 'name': name}
        )


mongo = MongoDB(
    AsyncMongoClient(config.mongo_url),
    config.mongodb.db,
    config.mongodb.collection,
)
