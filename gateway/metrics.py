from prometheus_client import Counter

REQUESTS_TOTAL = Counter(
    "requests_total",
    "Total requests handled"
)

RETRIES_TOTAL = Counter(
    "retries_total",
    "Total retries performed"
)

REQUESTS_BY_SERVER = Counter(
    "requests_by_server",
    "Requests forwarded to backend",
    ["server"]
)