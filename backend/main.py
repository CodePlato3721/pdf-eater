from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import ingestion, qa
from services.ingestion import PDFNotReadableError
from services.qa import NoDocumentLoadedError
from services.state import state


@asynccontextmanager
async def lifespan(app: FastAPI):
    ingestion.restore()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def get_status():
    return {"loaded": state.chain is not None, "files": state.loaded_files}


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)):
    payload = [(file.filename, await file.read()) for file in files]
    try:
        ingestion.ingest(payload)
    except PDFNotReadableError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return {"loaded": True, "files": state.loaded_files}


@app.get("/api/history")
def get_history():
    return {"history": state.chat_history}


@app.delete("/api/history")
def clear_history():
    state.clear_history()
    return {"history": []}


class AskRequest(BaseModel):
    question: str


@app.post("/api/ask")
def ask(request: AskRequest):
    try:
        answer = qa.ask(request.question)
    except NoDocumentLoadedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return {"answer": answer}
