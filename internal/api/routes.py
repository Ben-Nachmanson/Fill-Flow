from fastapi import APIRouter, HTTPException
from typing import List
from ..domain.models import OrderCreate, OrderResponse, HealthResponse
from ..storage.db import Database
from ..queue.publisher import OrderPublisher
from ..metrics import orders_created_total

router = APIRouter()

db = Database()
publisher = OrderPublisher()


@router.on_event("startup")
async def on_startup():
    await db.connect()
    await db.init_schema()


@router.on_event("shutdown")
async def on_shutdown():
    await db.disconnect()
    # close publisher redis client
    await publisher.close()


@router.post("/orders", response_model=OrderResponse)
async def create_order(payload: OrderCreate):
    # Persist order as NEW
    order = await db.create_order(payload)
    # instrument metric
    orders_created_total.inc()
    # Enqueue for fill simulation
    await publisher.publish_order(order)
    return order


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int):
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/orders", response_model=List[OrderResponse])
async def list_orders():
    return await db.get_orders()

@router.get("/positions")
async def get_positions():
    return await db.get_positions()
