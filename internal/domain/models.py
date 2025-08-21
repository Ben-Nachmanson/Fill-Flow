from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    NEW = "NEW"
    FILLED = "FILLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    id: int
    symbol: str
    side: Side
    qty: float
    price: float
    status: OrderStatus
    ts: datetime


@dataclass
class Fill:
    order_id: int
    price: float
    qty: float
    ts: datetime


@dataclass
class Position:
    symbol: str
    qty: float
    avg_price: float


# Pydantic schemas for API
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=16)
    side: Side
    qty: float = Field(..., gt=0)
    price: float = Field(..., gt=0)


class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: Side
    qty: float
    price: float
    status: OrderStatus
    ts: datetime


class HealthResponse(BaseModel):
    status: str
