from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.dao import search_by_embedding, get_text_embedding, update as data_upd
from app.req_models import ResumeAddingRequest, VacancyAddingRequest


router = APIRouter(tags=["rv_api"])


@router.get("/search_vac")
async def search_vac_by_resume(
    request: Request,
    text: str,
):
    """
    Search for nearest neighbors in
    the "vac" table based on the given text.

    Args:
        request (Request): The FastAPI request object.
        text (str): The resume text for which to search for nearest neighbors.

    Returns:
        JSONResponse: The search results as a JSON response,
        including the metadata information retrieved
        from the "vac" table and the "success" key with the value True.
    """
    q_emb = await get_text_embedding(text)

    result = await search_by_embedding(
        embedding=q_emb,
        type="vac",
        session=request.state.db,
        f_indexes=request.state.fd,
    )

    return JSONResponse(content=result | {"success": True})


@router.get("/search_res")
async def search_res_by_vacancy(
    request: Request,
    text: str,
):
    """
    Search for nearest neighbors in
    the "resume" table based on the given text.

    Args:
        request (Request): The FastAPI request object.
        text (str): The vacancy text for which to search for nearest neighbors.

    Returns:
        JSONResponse: The search results as a JSON response,
        including the metadata information retrieved
        from the "res" table and the "success" key with the value True.
    """
    q_emb = await get_text_embedding(text)

    result = await search_by_embedding(
        embedding=q_emb,
        type="res",
        session=request.state.db,
        f_indexes=request.state.fd,
    )

    return JSONResponse(content=result | {"success": True})


@router.post("/update_res")
async def update(
    request: Request,
    resume_info: ResumeAddingRequest,
):
    """
    Updates the PostgreSQL database table and
    Faiss index with the provided resume information.

    Args:
        request (Request): The FastAPI request object.
        resume_info (ResumeAddingRequest): The resume information
        to be added to the database.

    Returns:
        JSONResponse: A JSON response
        indicating the success of the update.
    """
    await data_upd(
        data_to_add=resume_info.model_dump(),
        type="res",
        session=request.state.db,
        f_indexes=request.state.fd,
    )

    return JSONResponse(content={"success": True})


@router.post("/update_vac")
async def update(
    request: Request,
    vacancy_info: VacancyAddingRequest,
):
    """
    Updates the PostgreSQL database table and
    Faiss index with the provided vacancy information.

    Args:
        request (Request): The FastAPI request object.
        resume_info (ResumeAddingRequest): The vacancy information
        to be added to the database.

    Returns:
        JSONResponse: A JSON response
        indicating the success of the update.
    """
    await data_upd(
        data_to_add=vacancy_info.model_dump(),
        type="vac",
        session=request.state.db,
        f_indexes=request.state.fd,
    )

    return JSONResponse(content={"success": True})
