from asyncio import Lock


class LeastConnectionsScheduler:

    def __init__(self):
        self.active_connections = {}
        self.lock = Lock()

    async def select_server(self, services):

        if not services:
            return None

        async with self.lock:

            for service in services:
                service_id = service["service_id"]

                if service_id not in self.active_connections:
                    self.active_connections[service_id] = 0

            selected = min(
                services,
                key=lambda s: self.active_connections[
                    s["service_id"]
                ]
            )

        # print("Before:", self.active_connections)

        self.active_connections[
            selected["service_id"]
        ] += 1

        # print("Selected:", selected["service_id"])
        print("Now:", self.active_connections)

        return selected

    async def release_server(self, service_id):

        async with self.lock:

            if (
                service_id in self.active_connections
                and self.active_connections[service_id] > 0
            ):
                self.active_connections[
                    service_id
                ] -= 1
        print("Released:", service_id)
        print("Now:", self.active_connections)