from fastapi import FastAPI
from app.routers import prep

app = FastAPI(title="Adaptive Document Prep")

# Register routers
app.include_router(prep.router)

@app.get("/health")
def health():
    return {"ok": True}