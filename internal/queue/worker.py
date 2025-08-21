import os
import json
import asyncio
import random
from datetime import datetime
import redis.asyncio as redis
from ..storage.db import Database

STREAM_NAME = os.getenv("ORDERS_STREAM", "orders-stream")
GROUP = os.getenv("ORDERS_GROUP", "fillers")
CONSUMER = os.getenv("ORDERS_CONSUMER", "worker-1")


async def process_message(db: Database, data: dict):
    # Deterministic-ish price fill; add small slippage
    price = float(data["price"]) * (1 + random.uniform(-0.001, 0.001))
    qty = float(data["qty"])
    await db.apply_fill(int(data["order_id"]), price, qty)


async def worker():
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    db = Database()
    await db.connect()
    await db.init_schema()

    # Create group if not exists
    try:
        await r.xgroup_create(STREAM_NAME, GROUP, id="0-0", mkstream=True)
    except Exception:
        pass

    while True:
        msgs = await r.xreadgroup(GROUP, CONSUMER, streams={STREAM_NAME: ">"}, count=10, block=5000)
        if not msgs:
            await asyncio.sleep(0.1)
            continue
        for _, entries in msgs:
            for msg_id, fields in entries:
                data = json.loads(fields.get("data").decode() if isinstance(fields.get("data"), (bytes, bytearray)) else fields.get("data"))
                await process_message(db, data)
                await r.xack(STREAM_NAME, GROUP, msg_id)


def main():
    asyncio.run(worker())


if __name__ == "__main__":
    main()
