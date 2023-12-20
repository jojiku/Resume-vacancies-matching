from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import status

from embedder_sbert import Embedder


router = APIRouter(tags=["embedder"])
embedder = Embedder()


@router.get("/search")
def search(user_text: str):
    """
    Process the user's text and
    return a JSON response.

    Args:
        user_text (str): The text provided by
        the user that needs to be processed.

    Returns:
        JSON response: A JSON response object with a status
        code of 200 and the content is the result of calling
        the `answer` method of the `Embedder` instance.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=embedder.answer(user_text)
    )
