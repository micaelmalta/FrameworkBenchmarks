import os
from operator import attrgetter

from sqlalchemy import select
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..models import Fortune, World
from .base import Base


class Orm(Base):
    """
    Connection using SQLAlchemy
    """

    ADDITIONAL_FORTUNE_ORM = Fortune(
        id=0, message="Additional fortune added at request time."
    )
    READ_SELECT_ORM = select(World.randomnumber)

    sort_fortunes_key = attrgetter("message")

    db_session: sessionmaker

    @staticmethod
    def pg_dsn(dialect=None) -> str:
        """
        :return: DSN url suitable for sqlalchemy and aiopg.
        """
        return str(
            URL.create(
                database="hello_world",
                password=os.getenv("PGPASS", "benchmarkdbpass"),
                host="tfb-database",
                port="5432",
                username=os.getenv("PGUSER", "benchmarkdbuser"),
                drivername="postgresql+{}".format(dialect)
                if dialect
                else "postgresql",
            )
        )

    async def connect(self):
        dsn = self.pg_dsn("asyncpg")
        engine = create_async_engine(
            dsn,
            future=True,
            pool_size=self.max_size,
            connect_args={
                "ssl": False  # NEEDED FOR NGINX-UNIT OTHERWISE IT FAILS
            },
        )
        self.db_session = sessionmaker(engine, class_=AsyncSession)

    async def single_database_view(self, id_):
        async with self.db_session() as sess:
            return await sess.scalar(
                select(World.randomnumber).filter_by(id=id_)
            )

    async def multiple_database_view(self, ids):
        result = []
        async with self.db_session() as sess:
            for id_ in ids:
                num = await sess.scalar(self.READ_SELECT_ORM.filter_by(id=id_))
                result.append({"id": id_, "randomNumber": num})
        return result

    async def fortunes_view(self):
        async with self.db_session() as sess:
            ret = await sess.execute(select(Fortune.id, Fortune.message))
            data = ret.all()

        data.append(self.ADDITIONAL_FORTUNE_ORM)
        data.sort(key=self.sort_fortunes_key)
        return data

    async def database_updates_views(self, updates):
        async with self.db_session.begin() as sess:
            for id_, number in updates:
                world = await sess.get(World, id_, populate_existing=True)
                world.randomnumber = number

    async def close(self):
        await self.db_session.close()
