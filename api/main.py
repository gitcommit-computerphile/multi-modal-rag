from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import chunks, documents, query, sessions
from db.session import init_db

app = FastAPI(title="Multimodal Document RAG", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)
app.include_router(sessions.router)
app.include_router(chunks.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}
