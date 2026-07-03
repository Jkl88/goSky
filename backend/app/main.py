from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import auth, links, oauthsky_sso, redirect

app = FastAPI(title="goSky — сократитель ссылок")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_public_origin,
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(oauthsky_sso.router)
app.include_router(links.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "gosky"}


app.include_router(redirect.router)
