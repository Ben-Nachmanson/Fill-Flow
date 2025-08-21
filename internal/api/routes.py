from fastapi import APIRouter, HTTPException
from typing import List
from ..domain.models import OrderCreate, OrderResponse, HealthResponse
from ..storage.db import Database
from ..queue.publisher import OrderPublisher

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


@router.post("/orders", response_model=OrderResponse)
async def create_order(payload: OrderCreate):
    # Persist order as NEW
    order = await db.create_order(payload)
    # Enqueue for fill simulation
    await publisher.publish_order(order)
    return order


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int):
    order = await db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/positions")
async def get_positions():
    return await db.get_positions()
