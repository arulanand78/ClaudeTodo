"""FastAPI application entrypoint (PRD §8).

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers import todos

app = FastAPI(title="ClaudeTodo API", version="1.0.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # PRD §5.3: invalid input is rejected with 400 and a { "detail": "..." } body.
    messages = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []) if p != "body")
        msg = err.get("msg", "invalid input")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=400,
        content={"detail": "; ".join(messages) or "invalid input"},
    )

# CORS: allow the Vite dev origin locally and any origin in production
# (Render frontend is a separate static-site domain). No auth/cookies in v1.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ClaudeTodo API is running"}