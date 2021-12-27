import os
from operator import itemgetter
from random import randint

import asyncpg

from fastapi import Depends, FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

try:
    import orjson

    from fastapi.responses import ORJSONResponse as JSONResponse
except ModuleNotFoundError:
    from fastapi.responses import JSONResponse


READ_ROW_SQL = 'SELECT "randomnumber", "id" FROM "world" WHERE id = $1'
WRITE_ROW_SQL = 'UPDATE "world" SET "randomnumber"=$1 WHERE id=$2'
ADDITIONAL_ROW = [0, "Additional fortune added at request time."]


async def get_database() -> asyncpg.pool.Pool:
    connection_pool = await asyncpg.create_pool(
        user=os.getenv("PGUSER", "benchmarkdbuser"),
        password=os.getenv("PGPASS", "benchmarkdbpass"),
        database="hello_world",
        host="tfb-database",
        port=5432,
        ssl=False,
    )
    try:
        yield connection_pool
    finally:
        await connection_pool.close()


templates = Jinja2Templates(directory="templates")


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


sort_fortunes_key = itemgetter(1)

app = FastAPI()


@app.get("/json")
async def json_serialization():
    return JSONResponse({"message": "Hello, world!"})


@app.get("/db")
async def single_database_query(
    connection_pool: asyncpg.pool.Pool = Depends(get_database),
):
    row_id = randint(1, 10000)

    async with connection_pool.acquire() as connection:
        number = await connection.fetchval(READ_ROW_SQL, row_id)

    return JSONResponse({"id": row_id, "randomNumber": number})


@app.get("/queries")
async def multiple_database_queries(
    queries=None, connection_pool: asyncpg.pool.Pool = Depends(get_database)
):

    num_queries = get_num_queries(queries)
    row_ids = [randint(1, 10000) for _ in range(num_queries)]
    worlds = []

    async with connection_pool.acquire() as connection:
        statement = await connection.prepare(READ_ROW_SQL)
        for row_id in row_ids:
            number = await statement.fetchval(row_id)
            worlds.append({"id": row_id, "randomNumber": number})

    return JSONResponse(worlds)


@app.get("/fortunes")
async def fortunes(
    request: Request,
    connection_pool: asyncpg.pool.Pool = Depends(get_database),
):
    async with connection_pool.acquire() as connection:
        data = await connection.fetch("SELECT * FROM Fortune")

    data.append(ADDITIONAL_ROW)
    data.sort(key=sort_fortunes_key)
    return templates.TemplateResponse(
        "fortune.html", {"request": request, "fortunes": data}
    )


@app.get("/updates")
async def database_updates(
    queries=None, connection_pool: asyncpg.pool.Pool = Depends(get_database)
):
    num_queries = get_num_queries(queries)
    updates = [
        (randint(1, 10000), randint(1, 10000)) for _ in range(num_queries)
    ]
    worlds = [
        {"id": row_id, "randomNumber": number} for row_id, number in updates
    ]

    async with connection_pool.acquire() as connection:
        statement = await connection.prepare(READ_ROW_SQL)
        for row_id, _ in updates:
            await statement.fetchval(row_id)
        await connection.executemany(WRITE_ROW_SQL, updates)

    return JSONResponse(worlds)


@app.get("/plaintext")
async def plaintext():
    return PlainTextResponse(b"Hello, world!")
