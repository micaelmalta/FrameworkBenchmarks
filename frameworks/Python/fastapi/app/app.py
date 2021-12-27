import os
from random import randint

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

try:
    import orjson

    from fastapi.responses import ORJSONResponse as JSONResponse
except ModuleNotFoundError:
    from fastapi.responses import UJSONResponse as JSONResponse


template_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "templates"
)
templates = Jinja2Templates(directory=template_path)

CONNECTION_RAW = os.getenv("CONNECTION", "RAW").upper() == "RAW"

app = FastAPI()


def get_num_queries(queries):
    try:
        query_count = int(queries)
    except (ValueError, TypeError):
        return 1

    if query_count < 1:
        return 1
    if query_count > 500:
        return 500
    return query_count


@app.on_event("startup")
async def startup_event():
    if CONNECTION_RAW:
        from .adapters.raw import Raw

        app.state.db = Raw()
    else:
        from .adapters.orm import Orm

        app.state.db = Orm()

    await app.state.db.connect()


@app.on_event("shutdown")
async def shutdown_event():
    await app.state.db.close()


@app.get("/json")
async def json_serialization():
    return JSONResponse({"message": "Hello, world!"})


@app.get("/db")
async def single_database_query():
    id_ = randint(1, 10000)
    number = await app.state.db.single_database_view(id_)

    return JSONResponse({"id": id_, "randomNumber": number})


@app.get("/queries")
async def multiple_database_queries(queries=None):
    num_queries = get_num_queries(queries)
    ids = [randint(1, 10000) for _ in range(num_queries)]
    result = await app.state.db.multiple_database_view(ids)

    return JSONResponse(result)


@app.get("/fortunes")
async def fortunes(request: Request):
    data = await app.state.db.fortunes_view()

    return templates.TemplateResponse(
        "fortune.jinja", {"request": request, "fortunes": data}
    )


@app.get("/updates")
async def database_updates(queries=None):
    num_queries = get_num_queries(queries)
    updates = [
        (randint(1, 10000), randint(1, 10000)) for _ in range(num_queries)
    ]
    updates.sort()
    worlds = [
        {"id": row_id, "randomNumber": number} for row_id, number in updates
    ]

    await app.state.db.database_updates_views(updates)

    return JSONResponse(worlds)


@app.get("/plaintext")
async def plaintext():
    return PlainTextResponse(b"Hello, world!")
