import logging
from contextlib import asynccontextmanager
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import database
from app.dao import init_db
import app.healthchecker as hc
from app.router import router


@asynccontextmanager
async def init_tables(app: FastAPI):
    hc.Readiness(urls=[os.getenv("EMBEDDER_URL")], logger=app.state.Logger).run()

    # Init DB tables if not exist
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
        await init_db(conn, database.fd)

    yield


app = FastAPI(
    title="R&V Search",
    description="Main Script for Resume and Vacancies search service",
    version="0.0.1",
    docs_url="/docs",
    redoc_url=None,
    lifespan=init_tables,
)

app.state.Logger = logging.getLogger(name="search_engine")
app.state.Logger.setLevel("DEBUG")

app.include_router(router)


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """
    Middleware function that manages the database
    session for each incoming request and closes
    the session after the response is sent.

    Args:
        request (Request): The incoming request object.

        call_next (function): The function to call
        the next middleware or the main application handler.

    Returns:
        Response: The response object returned by the
        next middleware or the main application handler.
    """
    request.state.db = database.async_session_maker()
    request.state.fd = database.fd
    try:
        response = await call_next(request)
    except Exception as exc:
        detail = getattr(exc, "detail", None)
        unexpected_error = not detail
        if unexpected_error:
            args = getattr(exc, "args", None)
            detail = args[0] if args else str(exc)
        app.state.Logger.error(detail, exc_info=unexpected_error)
        status_code = getattr(exc, "status_code", 500)
        response = JSONResponse(
            content={"detail": str(detail), "success": False}, status_code=status_code
        )
    finally:
        await request.state.db.close()

    return response


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8020,
    )
