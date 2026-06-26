import asyncio
import time

import httpx

URL = "http://localhost:8081/process"

TOTAL_REQUESTS = 10


async def send_request(client, request_id):

    start = time.perf_counter()

    try:

        response = await client.get(URL)

        elapsed = time.perf_counter() - start

        print(
            f"Request {request_id:02d} | "
            f"{response.status_code} | "
            f"{response.json()} | "
            f"{elapsed:.2f}s"
        )

    except Exception as e:

        print(
            f"Request {request_id:02d} FAILED -> {e}"
        )


async def main():

    async with httpx.AsyncClient(timeout=30) as client:

        tasks = [

            send_request(client, i)

            for i in range(1, TOTAL_REQUESTS + 1)

        ]

        await asyncio.gather(*tasks)


if __name__ == "__main__":

    asyncio.run(main())