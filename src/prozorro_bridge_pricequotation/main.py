from aiohttp import ClientSession
import asyncio
from prozorro_crawler.main import main
from prozorro_bridge_pricequotation.bridge import process_listing
from prozorro_bridge_pricequotation.settings import SENTRY_DSN


async def data_handler(session: ClientSession, items: list) -> None:
    process_items_tasks = []
    for item in items:
        coroutine = process_listing(session, item)
        process_items_tasks.append(coroutine)
    await asyncio.gather(*process_items_tasks)


if __name__ == "__main__":
    if SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(dsn=SENTRY_DSN)

    main(data_handler)
