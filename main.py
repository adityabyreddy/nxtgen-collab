from fastapi import FastAPI

from app import db
from app.api import router as api_router
from app.web import router as web_router

app = FastAPI(title="NxtGen Collab")
app.include_router(api_router)
app.include_router(web_router)


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
