from prometheus_client import Counter , Histogram , generate_latest , CONTENT_TYPE_LATEST , CollectorRegistry

from fastapi import Response , Request , FastAPI

from starlette.middleware.base import BaseHTTPMiddleware
import time

REQUEST_COUNTER = Counter(
    "HTTP_Request_Total",
    "HTTP Request Total",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "HTTP_Request_duration_seconds",
    "HTTP Request Latency ",
    ["method", "endpoint"],
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self , req : Request , call_next):
        start_time = time.time()
        resp = await call_next(req)
        latency = time.time() - start_time

        REQUEST_LATENCY.labels(
            method=req.method,
            endpoint=req.url.path
        ).observe(latency)

        REQUEST_COUNTER.labels(
            method=req.method,
            endpoint=req.url.path,
            status=resp.status_code
        ).inc()

        return resp

def setup_metrics(app : FastAPI):

    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics_qwertyuiopasdfghjkl",include_in_schema=False)
    def metrics_endpoint():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)