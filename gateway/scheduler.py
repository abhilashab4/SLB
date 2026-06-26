from asyncio import Lock
from typing import Dict, List, Optional


class LeastConnectionsScheduler:
    """
    Least Connections Scheduler

    Chooses the backend server currently handling
    the fewest active requests.
    """

    def __init__(self):
        self.active_connections: Dict[str, int] = {}
        self.lock = Lock()

    async def select_server(
        self,
        services: List[dict]
    ) -> Optional[dict]:

        if not services:
            return None

        async with self.lock:

            # Register new servers
            for service in services:
                service_id = service["service_id"]

                if service_id not in self.active_connections:
                    self.active_connections[service_id] = 0

            # Remove dead servers
            alive = {
                s["service_id"]
                for s in services
            }

            for server_id in list(self.active_connections.keys()):
                if server_id not in alive:
                    del self.active_connections[server_id]

            # Least connections
            selected = min(
                services,
                key=lambda s: self.active_connections[
                    s["service_id"]
                ]
            )

            self.active_connections[
                selected["service_id"]
            ] += 1

            return selected

    async def release_server(
        self,
        service_id: str
    ):

        async with self.lock:

            if service_id not in self.active_connections:
                return

            if self.active_connections[service_id] > 0:
                self.active_connections[
                    service_id
                ] -= 1

    async def get_connections(self):

        async with self.lock:
            return dict(self.active_connections)