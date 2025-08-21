import random
from typing import Dict


class RandomWalkPriceFeed:
    def __init__(self, start_prices: Dict[str, float] | None = None):
        self.prices: Dict[str, float] = start_prices or {"AAPL": 190.0, "MSFT": 420.0, "GOOG": 130.0}

    def tick(self, symbol: str) -> float:
        cur = self.prices.get(symbol, 100.0)
        cur *= 1 + random.uniform(-0.002, 0.002)
        cur = max(cur, 0.01)
        self.prices[symbol] = cur
        return cur
