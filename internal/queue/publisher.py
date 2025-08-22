import os
import json
import asyncio
import redis.asyncio as redis
from ..domain.models import Order

STREAM_NAME = os.getenv("ORDERS_STREAM", "orders-stream")


class OrderPublisher:
    def __init__(self) -> None:
        self._redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    async def publish_order(self, order: Order) -> None:
        payload = {
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "qty": order.qty,
            "price": order.price,
        }
        await self._redis.xadd(STREAM_NAME, {"data": json.dumps(payload)})

    async def close(self) -> None:
        """Close the async Redis client cleanly."""
        try:
            await self._redis.close()
        except Exception:
            # best-effort close; swallow errors during shutdown
            pass
