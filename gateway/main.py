import itertools
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from prometheus_client import generate_latest

from gateway.scheduler import LeastConnectionsScheduler
from gateway.registry_client import RegistryClient
from gateway.proxy import ProxyService
from gateway.circuit_breaker import CircuitBreaker
from gateway.metrics import (
    REQUESTS_TOTAL,
    RETRIES_TOTAL,
    REQUESTS_BY_SERVER
)

app = FastAPI()

scheduler = LeastConnectionsScheduler()
registry_client = RegistryClient()
request_counter = itertools.count(1)
proxy_service = ProxyService()
circuit_breaker = CircuitBreaker()


@app.get("/health")
async def health():
    return {
        "status": "gateway healthy"
    }


@app.get("/connections")
async def connections():
    return await scheduler.get_connections()


@app.get("/circuit-breaker")
async def circuit_breaker_status():
    return await circuit_breaker.get_status()


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(
        generate_latest().decode("utf-8")
    )


@app.api_route(
    "/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE"
    ]
)
async def gateway(
    request: Request,
    path: str
):
    services = await registry_client.get_services()

    if not services:
        return JSONResponse(
            status_code=503,
            content={
                "error": "No healthy servers available"
            }
        )

    body = await request.body()
    available_servers = []

    for service in services:
        if await circuit_breaker.is_available(
            service["service_id"]
        ):
            available_servers.append(service)

    if not available_servers:
        return JSONResponse(
            status_code=503,
            content={
                "error": "All circuits are open"
            }
        )

    # Track request ID once per incoming gateway call
    request_id = next(request_counter)

    for attempt in range(len(available_servers)):

        selected_server = await scheduler.select_server(
            available_servers
        )

        REQUESTS_TOTAL.inc()

        REQUESTS_BY_SERVER.labels(
            server=selected_server["service_id"]
        ).inc()

        target_url = (
            f"{selected_server['url']}{path}"
        )

        try:
            print("\n" + "=" * 70)
            print(f"REQUEST #{request_id} (Attempt {attempt + 1})")
            print("=" * 70)

            print(f"Method          : {request.method}")
            print(f"Path            : {request.url.path}")
            print(f"Selected Server : {selected_server['service_id']}")

            # Fetch active connections immediately before printing
            connections = await scheduler.get_connections()
            print("\nActive Connections")

            for server, count in connections.items():
                print(f"  {server:<10} -> {count}")

            start_time = time.perf_counter()

            response = await proxy_service.forward(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                params=request.query_params,
                body=body
            )

            if response.status_code >= 500:
                raise Exception(
                    f"Backend error "
                    f"{response.status_code}"
                )

            await circuit_breaker.record_success(
                selected_server["service_id"]
            )

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print("\nStatus          : SUCCESS")
            print(
                f"Response Time   : "
                f"{elapsed:.3f} sec"
            )
            print("=" * 70)

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except Exception as e:
            RETRIES_TOTAL.inc()

            await circuit_breaker.record_failure(
                selected_server["service_id"]
            )

            print("\nStatus          : FAILED")
            print("Retrying        : YES")
            print("=" * 70)

            print(
                f"Retrying after failure: "
                f"{selected_server['service_id']}"
            )

            available_servers.remove(
                selected_server
            )

        finally:
            await scheduler.release_server(
                selected_server["service_id"]
            )

    return JSONResponse(
        status_code=503,
        content={
            "error": "All backend servers unavailable"
        }
    )