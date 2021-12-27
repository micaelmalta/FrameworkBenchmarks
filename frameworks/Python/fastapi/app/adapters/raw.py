import os
from operator import itemgetter

import asyncpg

from .base import Base


class Raw(Base):
    """
    Connection using AsyncPG
    """

    READ_ROW_SQL = 'SELECT "randomnumber", "id" FROM "world" WHERE id = $1'
    WRITE_ROW_SQL = 'UPDATE "world" SET "randomnumber" = $2 WHERE id = $1'
    ADDITIONAL_FORTUNE_ROW = {
        "id": 0,
        "message": "Additional fortune added at request time.",
    }

    sort_fortunes_key = itemgetter("message")

    db_session: asyncpg.pool.Pool

    async def connect(self):
        self.db_session = await asyncpg.create_pool(
            user=os.getenv("PGUSER", "benchmarkdbuser"),
            password=os.getenv("PGPASS", "benchmarkdbpass"),
            database="hello_world",
            host="tfb-database",
            port=5432,
            min_size=self.min_size,
            max_size=self.max_size,
            ssl=False,  # NEEDED FOR NGINX-UNIT OTHERWISE IT FAILS
        )

    async def single_database_view(self, id_):
        async with self.db_session.acquire() as connection:
            return await connection.fetchval(self.READ_ROW_SQL, id_)

    async def multiple_database_view(self, ids):
        results = []
        async with self.db_session.acquire() as connection:
            statement = await connection.prepare(self.READ_ROW_SQL)
            for row_id in ids:
                number = await statement.fetchval(row_id)
                results.append({"id": row_id, "randomNumber": number})
        return results

    async def fortunes_view(self):
        async with self.db_session.acquire() as connection:
            data = await connection.fetch("SELECT * FROM Fortune")
        data.append(self.ADDITIONAL_FORTUNE_ROW)
        data.sort(key=self.sort_fortunes_key)
        return data

    async def database_updates_views(self, updates):
        async with self.db_session.acquire() as connection:
            statement = await connection.prepare(self.READ_ROW_SQL)
            for row_id, _ in updates:
                await statement.fetchval(row_id)

            await connection.executemany(self.WRITE_ROW_SQL, updates)

    async def close(self):
        await self.db_session.close()
