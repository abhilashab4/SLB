from fastapi import FastAPI
from fastapi import Request

from fastapi.responses import (
    JSONResponse,
    Response
)

from gateway.scheduler import (
    LeastConnectionsScheduler,
)

from gateway.registry_client import (
    RegistryClient
)

from gateway.proxy import (
    ProxyService
)

app = FastAPI()

scheduler = LeastConnectionsScheduler()

registry_client = RegistryClient()

proxy_service = ProxyService()


@app.get("/health")
async def health():

    return {
        "status": "gateway healthy"
    }


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
                "error":
                "No healthy servers available"
            }
        )

    body = await request.body()

    available_servers = services.copy()

    for _ in range(len(available_servers)):

        selected_server = await scheduler.select_server(
            available_servers
        )

        target_url = (
            f"{selected_server['url']}{path}"
        )

        try:

            print(
                f"Forwarding to "
                f"{selected_server['service_id']}"
            )

            # Debug only
            # print(
            #     "Selected:",
            #     selected_server["service_id"]
            # )
            #
            # print(
            #     "Connections:",
            #     scheduler.active_connections
            # )

            response = await proxy_service.forward(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                params=request.query_params,
                body=body
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except Exception as e:

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
            "error":
            "All backend servers unavailable"
        }
    )


@app.get("/connections")
async def connections():

    return scheduler.active_connections