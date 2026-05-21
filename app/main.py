from fastapi import FastAPI
app = FastAPI(title="Adaptive Document Prep")
@app.get("/health") # quick liveness endpoint
def health(): return {"ok": True}
