import asyncio
from prozorro_bridge_pricequotation.settings import LOGGER, ERROR_INTERVAL
from prozorro_bridge_pricequotation.journal_msg_ids import MONGODB_EXCEPTION
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from typing import Callable
from prozorro_bridge_pricequotation.settings import (
    MONGODB_PRICEQUOTATION_COLLECTION,
    MONGODB_DATABASE,
    MONGODB_URL,
)


def retry_decorator(log_message: str = None) -> Callable:
    def outer(func: Callable) -> Callable:
        async def inner(*args, **kwargs) -> None:
            while True:
                try:
                    await func(*args, **kwargs)
                    break
                except PyMongoError as e:
                    LOGGER.warning({"message": log_message, "error": e}, extra={"MESSAGE_ID": MONGODB_EXCEPTION})
                    await asyncio.sleep(ERROR_INTERVAL)
        return inner
    return outer


class Db:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = getattr(self.client, MONGODB_DATABASE)
        self.collection = getattr(self.db, MONGODB_PRICEQUOTATION_COLLECTION)

    @retry_decorator(log_message="Has collection")
    async def has_collection(self, tender_id: str) -> bool:
        value = await self.collection.find_one({"_id": tender_id})
        return value is not None

    @retry_decorator(log_message="Cache collection")
    async def cache_collection(self, tender_id: str, date_modified: str) -> None:
        await self.collection.insert_one(
            {"_id": tender_id, "dateModified": date_modified}
        )


cache_db = Db()
