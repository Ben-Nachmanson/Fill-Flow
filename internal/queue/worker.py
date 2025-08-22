import os
import json
import asyncio
import random
import logging
from datetime import datetime
import redis.asyncio as redis
from ..storage.db import Database
from ..pricing.price_feed import RandomWalkPriceFeed
from ..metrics import orders_filled_total

logger = logging.getLogger("worker")

STREAM_NAME = os.getenv("ORDERS_STREAM", "orders-stream")
GROUP = os.getenv("ORDERS_GROUP", "fillers")
CONSUMER = os.getenv("ORDERS_CONSUMER", "worker-1")


async def process_message(db: Database, data: dict):
    # Deterministic-ish price fill; add small slippage
    price = float(data["price"]) * (1 + random.uniform(-0.001, 0.001))
    qty = float(data["qty"])
    await db.apply_fill(int(data["order_id"]), price, qty)
    # instrument metric
    orders_filled_total.inc()


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

    price_feed = RandomWalkPriceFeed()

    try:
        while True:
            msgs = await r.xreadgroup(GROUP, CONSUMER, streams={STREAM_NAME: ">"}, count=10, block=5000)
            if not msgs:
                # If no messages, optionally tick the price feed and continue
                await asyncio.sleep(0.1)
                continue
            for _, entries in msgs:
                for msg_id, fields in entries:
                    raw = fields.get("data")
                    if raw is None:
                        logger.warning("message %s missing 'data' field; acking and skipping", msg_id)
                        try:
                            await r.xack(STREAM_NAME, GROUP, msg_id)
                        except Exception:
                            logger.exception("failed to ack message %s", msg_id)
                        continue

                    try:
                        if isinstance(raw, (bytes, bytearray)):
                            raw = raw.decode()
                        data = json.loads(raw)
                    except Exception:
                        logger.exception("failed to parse message %s: %r", msg_id, raw)
                        # ack bad message so it doesn't block the stream
                        try:
                            await r.xack(STREAM_NAME, GROUP, msg_id)
                        except Exception:
                            logger.exception("failed to ack bad message %s", msg_id)
                        continue

                    try:
                        await process_message(db, data)
                        await r.xack(STREAM_NAME, GROUP, msg_id)
                    except Exception:
                        logger.exception("error processing message %s", msg_id)
                        # don't ack so it can be retried / claimed

    except asyncio.CancelledError:
        # graceful cancellation
        pass
    except KeyboardInterrupt:
        # allow Ctrl+C
        pass
    finally:
        try:
            # prefer async close API if available (redis>=5.0.1 uses aclose)
            close_fn = getattr(r, "aclose", None)
            if close_fn:
                await close_fn()
            else:
                await r.close()
        except Exception:
            pass
        try:
            await db.disconnect()
        except Exception:
            pass


def main():
    asyncio.run(worker())


if __name__ == "__main__":
    main()
