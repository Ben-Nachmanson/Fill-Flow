import os
import asyncpg
from typing import Optional, List
from datetime import datetime
from ..domain.models import Order, OrderCreate, OrderStatus, Fill, Position, Side


class Database:
    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self._pool = await asyncpg.create_pool(
            user=os.getenv("DB_USER", "trade"),
            password=os.getenv("DB_PASSWORD", "trade"),
            database=os.getenv("DB_NAME", "trade"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            min_size=1,
            max_size=10,
        )

    async def disconnect(self):
        if self._pool:
            await self._pool.close()

    async def init_schema(self):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                create table if not exists orders(
                    id serial primary key,
                    symbol text not null,
                    side text not null,
                    qty double precision not null,
                    price double precision not null,
                    status text not null,
                    ts timestamptz not null default now()
                );
                create table if not exists fills(
                    id serial primary key,
                    order_id int not null references orders(id),
                    price double precision not null,
                    qty double precision not null,
                    ts timestamptz not null default now()
                );
                create table if not exists positions(
                    symbol text primary key,
                    qty double precision not null,
                    avg_price double precision not null
                );
                """
            )

    async def create_order(self, payload: OrderCreate) -> Order:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                insert into orders(symbol, side, qty, price, status)
                values($1, $2, $3, $4, $5)
                returning id, symbol, side, qty, price, status, ts
                """,
                payload.symbol,
                payload.side.value,
                float(payload.qty),
                float(payload.price),
                OrderStatus.NEW.value,
            )
            return Order(
                id=row["id"],
                symbol=row["symbol"],
                side=Side(row["side"]),
                qty=row["qty"],
                price=row["price"],
                status=OrderStatus(row["status"]),
                ts=row["ts"],
            )

    async def get_order(self, order_id: int) -> Optional[Order]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "select id, symbol, side, qty, price, status, ts from orders where id=$1",
                order_id,
            )
            if not row:
                return None
            return Order(
                id=row["id"],
                symbol=row["symbol"],
                side=Side(row["side"]),
                qty=row["qty"],
                price=row["price"],
                status=OrderStatus(row["status"]),
                ts=row["ts"],
            )

    async def get_orders(self) -> List[Order]:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "select id, symbol, side, qty, price, status, ts from orders order by id"
            )
            return [
                Order(
                    id=r["id"],
                    symbol=r["symbol"],
                    side=Side(r["side"]),
                    qty=r["qty"],
                    price=r["price"],
                    status=OrderStatus(r["status"]),
                    ts=r["ts"],
                )
                for r in rows
            ]

    async def get_positions(self):
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("select symbol, qty, avg_price from positions order by symbol")
            return [
                {"symbol": r["symbol"], "qty": r["qty"], "avg_price": r["avg_price"]}
                for r in rows
            ]

    async def apply_fill(self, order_id: int, price: float, qty: float) -> None:
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "insert into fills(order_id, price, qty) values($1,$2,$3)",
                    order_id,
                    price,
                    qty,
                )
                await conn.execute(
                    "update orders set status=$2 where id=$1",
                    order_id,
                    OrderStatus.FILLED.value,
                )
                # upsert position
                row = await conn.fetchrow(
                    "select symbol, side, qty, price from orders where id=$1",
                    order_id,
                )
                symbol = row["symbol"]
                side = Side(row["side"])
                signed_qty = qty if side == Side.BUY else -qty
                existing = await conn.fetchrow(
                    "select qty, avg_price from positions where symbol=$1",
                    symbol,
                )
                if not existing:
                    await conn.execute(
                        "insert into positions(symbol, qty, avg_price) values($1,$2,$3)",
                        symbol,
                        signed_qty,
                        price,
                    )
                else:
                    cur_qty = existing["qty"]
                    cur_avg = existing["avg_price"]
                    new_qty = cur_qty + signed_qty
                    if abs(new_qty) < 1e-9:
                        # flat
                        await conn.execute(
                            "update positions set qty=0, avg_price=$2 where symbol=$1",
                            symbol,
                            0.0,
                        )
                    elif (cur_qty >= 0 and signed_qty >= 0) or (cur_qty <= 0 and signed_qty <= 0):
                        # same direction → weighted average
                        new_avg = (cur_qty * cur_avg + signed_qty * price) / new_qty
                        await conn.execute(
                            "update positions set qty=$2, avg_price=$3 where symbol=$1",
                            symbol,
                            new_qty,
                            new_avg,
                        )
                    else:
                        # reducing/reversing; keep avg the same if crosses through zero
                        await conn.execute(
                            "update positions set qty=$2 where symbol=$1",
                            symbol,
                            new_qty,
                        )
