from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Crypts and Commits Demo API",
    description="A Coding Assistant Continuity Framework. Demonstration API",
)

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Crypts and Commits Demo API</title>
</head>
<body>
    <h1>Crypts and Commits Demo API</h1>
    <p><a href="/docs">API documentation (Swagger UI)</a></p>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/health")
def health() -> dict[str, bool]:
    return {"success": True}
