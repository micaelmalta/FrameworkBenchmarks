import multiprocessing


class Base:
    min_size = 10
    max_size = 10

    def __init__(self):
        # number of workers = multiprocessing.cpu_count()
        # max_connections = 2000 as per toolset/setup/linux/databases/postgresql/postgresql.conf:64
        # give 10% leeway
        self.max_size = min(1800 / multiprocessing.cpu_count(), 160)
        self.max_size = max(int(self.max_size), 1)
        self.min_size = max(int(self.max_size / 2), 1)
        print(
            f"connection pool: min size: {self.min_size}, max size: {self.max_size}"
        )

    async def connect(self):
        raise NotImplementedError()

    async def close(self):
        raise NotImplementedError()

    async def single_database_view(self, id_):
        raise NotImplementedError()

    async def multiple_database_view(self, ids):
        raise NotImplementedError()

    async def fortunes_view(self):
        raise NotImplementedError()

    async def database_updates_views(self, updates):
        raise NotImplementedError()
