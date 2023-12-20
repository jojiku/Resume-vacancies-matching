import uvicorn
from fastapi import FastAPI

from router import router as root_router


app = FastAPI(
    title="Search Embedder",
    description="Input requests embedder for R&V",
    version="0.0.1",
    docs_url="/docs",
    redoc_url=None,
)

app.include_router(root_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
