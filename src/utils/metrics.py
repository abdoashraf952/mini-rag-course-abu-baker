from prometheus_client import Counter , Histogram , generate_latest , CONTENT_TYPE_LATEST , CollectorRegistry

from fastapi import Response , Request , FastAPI

from starlette.middleware.base import BaseHTTPMiddleware
from helpers.config import get_settings
import time

_app_name = get_settings().APP_NAME

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "HTTP Request Total",
    ["method", "path", "status", "app_name"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP Request Latency ",
    ["method", "path", "app_name"],
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self , req : Request , call_next):
        start_time = time.time()
        resp = await call_next(req)
        latency = time.time() - start_time

        REQUEST_LATENCY.labels(
            method=req.method,
            path=req.url.path,
            app_name=_app_name
        ).observe(latency)

        REQUEST_COUNTER.labels(
            method=req.method,
            path=req.url.path,
            status=resp.status_code,
            app_name=_app_name
        ).inc()

        return resp

def setup_metrics(app : FastAPI):

    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics_qwertyuiopasdfghjkl",include_in_schema=False)
    def metrics_endpoint():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
