import prometheus_client
from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST


async def metrics(request):
    resp = web.Response(body=prometheus_client.generate_latest())
    resp.content_type = CONTENT_TYPE_LATEST
    return resp
