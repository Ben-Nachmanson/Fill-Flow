import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from .routes import router as api_router

logger = logging.getLogger("trade-svc")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="trade-svc")

# Prometheus metrics
registry = CollectorRegistry()
Instrumentator().instrument(app).expose(app)


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"


app.include_router(api_router)
