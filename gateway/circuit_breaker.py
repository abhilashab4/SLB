import asyncio
import time
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:

    def __init__(self):

        self.failure_count = {}
        self.state = {}
        self.last_failure_time = {}

        # Prevent multiple requests entering HALF_OPEN
        self.half_open_in_progress = set()

        self.lock = asyncio.Lock()

        self.FAILURE_THRESHOLD = 3
        self.RESET_TIMEOUT = 20

    async def is_available(
        self,
        service_id: str
    ) -> bool:

        async with self.lock:

            state = self.state.get(
                service_id,
                CircuitState.CLOSED
            )

            if state == CircuitState.CLOSED:
                return True

            if state == CircuitState.OPEN:

                last_failure = self.last_failure_time.get(
                    service_id,
                    0
                )

                if (
                    time.monotonic() - last_failure
                    >= self.RESET_TIMEOUT
                ):

                    if service_id in self.half_open_in_progress:
                        return False

                    self.state[service_id] = (
                        CircuitState.HALF_OPEN
                    )

                    self.half_open_in_progress.add(
                        service_id
                    )

                    print(
                        f"[Circuit] {service_id} -> HALF_OPEN"
                    )

                    return True

                return False

            if state == CircuitState.HALF_OPEN:

                return (
                    service_id
                    in self.half_open_in_progress
                )

            return True

    async def record_success(
        self,
        service_id: str
    ):

        async with self.lock:

            old_state = self.state.get(
                service_id,
                CircuitState.CLOSED
            )

            self.failure_count[service_id] = 0

            self.state[service_id] = (
                CircuitState.CLOSED
            )

            self.half_open_in_progress.discard(
                service_id
            )

            if old_state != CircuitState.CLOSED:
                print(
                    f"[Circuit] {service_id} -> CLOSED"
                )

    async def record_failure(
        self,
        service_id: str
    ):

        async with self.lock:

            old_state = self.state.get(
                service_id,
                CircuitState.CLOSED
            )

            self.half_open_in_progress.discard(
                service_id
            )

            if old_state == CircuitState.HALF_OPEN:

                self.state[service_id] = (
                    CircuitState.OPEN
                )

                self.last_failure_time[
                    service_id
                ] = time.monotonic()

                print(
                    f"[Circuit] {service_id} -> OPEN (HALF_OPEN probe failed)"
                )

                return

            failures = (
                self.failure_count.get(
                    service_id,
                    0
                ) + 1
            )

            self.failure_count[
                service_id
            ] = failures

            self.last_failure_time[
                service_id
            ] = time.monotonic()

            print(
                f"[Circuit] Failure {failures} ({service_id})"
            )

            if (
                failures >= self.FAILURE_THRESHOLD
                and old_state != CircuitState.OPEN
            ):

                self.state[
                    service_id
                ] = CircuitState.OPEN

                print(
                    f"[Circuit] {service_id} -> OPEN"
                )

    async def get_status(self):

        async with self.lock:

            return {
                "state": {
                    k: v.value
                    for k, v in self.state.items()
                },
                "failures": dict(
                    self.failure_count
                )
            }