from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import debug, health, papers

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://lit-review-app.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Keywords"],
)
app.include_router(health.router)
app.include_router(papers.router)
app.include_router(debug.router)
