from fastapi import FastAPI
from fastapi.responses import Response

from app.api.v1.movements import router as movements_router

app = FastAPI()

app.include_router(movements_router, prefix="/api", tags=["Движение товаров"])

# @app.get("/health")
# def check():
#     return Response(status_code=200)
