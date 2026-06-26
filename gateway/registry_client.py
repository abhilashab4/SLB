import httpx

REGISTRY_URL = "http://registry:8000"


class RegistryClient:

    async def get_services(self):

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{REGISTRY_URL}/services"
            )

            response.raise_for_status()

            return response.json()