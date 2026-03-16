from mangum import Mangum
from api.main import app

handler = Mangum(
    app,
    lifespan="off",
    text_mime_types=[
        "application/json",
        "application/javascript",
        "application/xml",
        "application/vnd.api+json",
        "text/html",
        "text/plain",
        "text/css",
        "text/javascript",
        "text/xml",
    ]
)