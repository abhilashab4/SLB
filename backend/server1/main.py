from fastapi import FastAPI

from backend.common.registration import (
    register_service
)

from backend.common.heartbeat import (
    start_heartbeat
)

import asyncio

app = FastAPI()

SERVICE_ID = "server1"

SERVICE_URL = "http://localhost:8001"

REGISTRY_URL = "http://localhost:9000"


@app.on_event("startup")
async def startup():

    register_service(
        REGISTRY_URL,
        SERVICE_ID,
        SERVICE_URL
    )

    start_heartbeat(
        REGISTRY_URL,
        SERVICE_ID
    )


@app.get("/")
async def root():

    return {
        "server": SERVICE_ID
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "server": SERVICE_ID
    }

@app.get("/process")
async def process():

    await asyncio.sleep(20)

    return {
        "processed_by": SERVICE_ID
    }

# @app.get("/process")
# async def process():

#     return {
#         "processed_by": SERVICE_ID
#     }