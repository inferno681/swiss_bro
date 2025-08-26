from beanie import init_beanie
from pymongo import AsyncMongoClient

from bot.model import Product, User
from config import config

client: AsyncMongoClient = AsyncMongoClient(config.mongo_url)


async def init_db():
    await init_beanie(
        database=client[config.mongodb.db], document_models=[User, Product]
    )
