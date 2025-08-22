from prometheus_client import Counter

# Prometheus counters
orders_created_total = Counter("orders_created_total", "Total orders created")
orders_filled_total = Counter("orders_filled_total", "Total orders filled")
