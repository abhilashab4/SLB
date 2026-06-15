import time


class CircuitBreaker:

    def __init__(self):

        self.failure_count = {}

        self.state = {}

        self.last_failure_time = {}

        self.FAILURE_THRESHOLD = 3

        self.RESET_TIMEOUT = 20

    def is_available(self, service_id):

        state = self.state.get(
            service_id,
            "CLOSED"
        )

        if state == "OPEN":

            last_failure = (
                self.last_failure_time.get(
                    service_id,
                    0
                )
            )

            if (
                time.time()
                - last_failure
                > self.RESET_TIMEOUT
            ):

                self.state[
                    service_id
                ] = "HALF_OPEN"

                print(
                    f"HALF_OPEN: "
                    f"{service_id}"
                )

                return True

            return False

        return True

    def record_success(
        self,
        service_id
    ):

        self.failure_count[
            service_id
        ] = 0

        self.state[
            service_id
        ] = "CLOSED"

        print(
            f"CLOSED: "
            f"{service_id}"
        )

    def record_failure(
        self,
        service_id
    ):

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
        ] = time.time()

        print(
            f"Failure {failures}: "
            f"{service_id}"
        )

        if (
            failures
            >= self.FAILURE_THRESHOLD
        ):

            self.state[
                service_id
            ] = "OPEN"

            print(
                f"OPEN CIRCUIT: "
                f"{service_id}"
            )

    def get_status(self):

        return {
            "state": self.state,
            "failures": self.failure_count
        }