import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import faiss
import orjson

import app.config as config


class Base(DeclarativeBase):
    pass


def orjson_serializer(obj) -> bytes:
    """
    Orjson serializer.

    :param obj: An object to be serialized.
    """
    return orjson.dumps(obj, option=orjson.OPT_NAIVE_UTC).decode()


db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
postgres_url = (
    f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
)

engine = create_async_engine(
    postgres_url,  # TODO
    json_serializer=orjson_serializer,
    json_deserializer=orjson.loads,
)
async_session_maker = sessionmaker(engine, class_=AsyncSession)

f_index_res = faiss.IndexFlatL2(512)  # hardcoded 384, 512
if os.path.exists(config.path_to_res_index):
    f_index_res = faiss.read_index(config.path_to_res_index)

f_index_vac = faiss.IndexFlatL2(512)  # hardcoded
if os.path.exists(config.path_to_vac_index):
    f_index_vac = faiss.read_index(config.path_to_vac_index)

fd = {
    "res": [f_index_res, config.path_to_res_index],
    "vac": [f_index_vac, config.path_to_vac_index],
}
