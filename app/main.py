from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Pokemon Team Generator")

app.include_router(router)
