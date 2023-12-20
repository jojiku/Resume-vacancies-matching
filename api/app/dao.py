import os
from itertools import chain
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from fastapi import status
import faiss
import numpy as np
import pandas as pd
import sqlalchemy as sa
import aiohttp

from app.pg_models import Resumes, Vacancies
import app.config as config
from app.database import Base


TYPE_TABLE = {
    "res": [Resumes, config.res_faiss_func],
    "vac": [Vacancies, config.vac_faiss_func],
}


async def get_text_embedding(text):
    """
    Retrieves the embedding vector for a given
    text by sending a GET request to an embedding service API.

    Args:
        text (str): The text for which the
        embedding will be retrieved.

    Returns:
        list: The embedding vector of the query text.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{os.getenv('EMBEDDER_URL')}/search?user_text={text}"
        ) as resp:
            responce = await resp.json()

    return responce["query_embedding"]


def faiss_search_result(query_embedding, f_index: faiss.IndexFlatL2):
    """
    Find the nearest neighbor embedding IDs and
    distances for a given query embedding using a Faiss index.

    Args:
        query_embedding (list): The embedding vector of the query.

        f_index (faiss.IndexFlatL2): The Faiss index used for searching.

    Returns:
        tuple: A tuple containing two lists:
            - embedding_ids (list): A list of embedding IDs
            of the nearest neighbors.
            - embedding_distances (list): A list of distances between
            the query embedding and the nearest neighbors.
    """
    embedding_distances, embedding_ids = f_index.search(
        np.array([query_embedding]).astype("float32"), config.topn
    )
    return embedding_ids[0], embedding_distances[0]


async def insert_data_to_pg(cols, table: Base, session: AsyncSession):
    """
    Insert data into a PostgreSQL database
    table using SQLAlchemy and return the primary key of the inserted row.

    Args:
        cols (tuple): A tuple representing the
        values to be inserted into the table.

        table (Base): The SQLAlchemy Base object
        representing the database table.

        session (AsyncSession): An AsyncSession object
        representing the database session.

    Returns:
        int: The primary key of the
        inserted row in the database table.
    """
    q = sa.insert(table).values(cols).returning(table.p_id)
    q = await session.execute(q)
    p_id = q.scalar_one_or_none()

    return p_id


async def insert_data(
    row: dict,
    faiss_str: str,
    table: Base,
    session: AsyncSession,
    f_index: faiss.IndexFlatL2,
):
    """
    Insert data into a PostgreSQL database table and update a Faiss index.

    Args:
        row (dict): A dictionary representing the
        values to be inserted into the table.

        faiss_str (str): A string representing the text
        for which the embedding will be retrieved.

        table (Base): The SQLAlchemy Base object
        representing the database table.

        session (AsyncSession): An AsyncSession object
        representing the database session.

        f_index (faiss.IndexFlatL2): A Faiss IndexFlatL2 object
        representing the Faiss index.

    Returns:
        int: The primary key of the inserted row in the database table.
    """
    f_id = f_index.ntotal

    e = await get_text_embedding(faiss_str)
    embedding = np.array([e]).astype("float32")
    f_index.add(embedding)

    await insert_data_to_pg(
        cols=tuple([f_id]) + tuple(row.values()), table=table, session=session
    )


async def init_db(
    session: AsyncSession, f_indexes: dict[str, tuple[faiss.IndexFlatL2, str]]
):
    """
    Initializes the database by inserting data from CSV files
    into corresponding database tables and updating Faiss indexes.

    Args:
        session (AsyncSession): An AsyncSession object
        representing the database session.

        f_indexes (dict[str, tuple[faiss.IndexFlatL2, str]]): A dictionary
        containing Faiss indexes and their corresponding column names as values.

    Returns:
        None
    """
    if any(fi[0].ntotal for fi in f_indexes.values()):
        return

    res = pd.read_csv(config.path_to_res)
    res = res.fillna("")
    res = res.astype(str)
    res = res.sample(n=1000)
    res["type"] = "res"

    vac = pd.read_csv(config.path_to_vac)
    vac = vac.fillna("")
    vac = vac.astype(str)
    vac = vac.sample(n=1000)
    vac["type"] = "vac"

    if res.empty or vac.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is broken or wrong columns are specified",
        )

    for _, row in chain(res.iterrows(), vac.iterrows()):
        _cls, faiss_str_func = TYPE_TABLE[row["type"]]

        await insert_data(
            row=row.drop(labels=["type"]).to_dict(),
            faiss_str=faiss_str_func(row),
            table=_cls,
            session=session,
            f_index=f_indexes[row["type"]][0],
        )

    for _, v in f_indexes.items():
        faiss.write_index(v[0], v[1])
        v[0] = faiss.read_index(v[1])

    await session.commit()


async def get_metainf_by_text(table: Base, faiss_id, session: AsyncSession):
    """
    Retrieves metadata information from a
    database table based on a given ID.

    Args:
        table (Base): A SQLAlchemy table object
        representing the database table.

        faiss_id: The ID of the record in the table.

        session (AsyncSession): An asynchronous database session object.

    Returns:
        dict: A dictionary containing the metadata information
        retrieved from the database table.
        The keys of the dictionary are the column names of the table,
        and the values are the corresponding attribute
        values of the retrieved record.
    """
    q = sa.select(table).where(table.p_id == faiss_id)
    q = await session.execute(q)
    res = q.fetchone()[0]

    return {c.name: str(getattr(res, c.name)) for c in res.__table__.columns}


async def search_by_embedding(
    embedding,
    type,
    session: AsyncSession,
    f_indexes: dict[str, tuple[faiss.IndexFlatL2, str]],
):
    """
    Retrieve metadata information from a
    database table based on a given embedding.

    Args:
        embedding (list): The embedding vector for
        which to search for nearest neighbors.

        type (str): The type of the embedding, which
        determines the database table to query.

        session (AsyncSession): An asynchronous
        database session object.

        f_indexes (dict[str, tuple[faiss.IndexFlatL2, str]]): A dictionary mapping the
        embedding type to a tuple containing the Faiss index and the index name.

    Returns:
        dict: A dictionary containing the metadata information
        retrieved from the database table. The keys of the dictionary
        are the column names of the table, and the values are the
        corresponding attribute values of the retrieved record.
    """
    f_index = f_indexes[type][0]
    embedding_ids, _ = faiss_search_result(embedding, f_index)

    res_dict = defaultdict(list)
    for index_id in embedding_ids:
        _cls, _ = TYPE_TABLE[type]

        metainfo = await get_metainf_by_text(_cls, index_id, session)
        if not metainfo:
            continue

        for k, v in metainfo.items():
            res_dict[k].append(v)

    return res_dict


async def update(
    data_to_add,
    type,
    session: AsyncSession,
    f_indexes: dict[str, tuple[faiss.IndexFlatL2, str]],
):
    """
    Insert data into a PostgreSQL database table
    and update a Faiss index.

    Args:
        data_to_add: A dictionary representing the
        data to be inserted into the database table.

        type: A string representing the type of data (resumes or vacancies).

        session: An AsyncSession object representing the database session.

        f_indexes: A dictionary containing Faiss indexes
        for different types of data.

    Returns:
        None
    """
    _cls, faiss_str_func = TYPE_TABLE[type]

    await insert_data(
        row=data_to_add,
        faiss_str=faiss_str_func(data_to_add),
        table=_cls,
        session=session,
        f_index=f_indexes[type][0],
    )

    for _, v in f_indexes.items():
        faiss.write_index(v[0], v[1])
        v[0] = faiss.read_index(v[1])

    await session.commit()
