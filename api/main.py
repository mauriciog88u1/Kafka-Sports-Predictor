from fastapi import FastAPI

app = FastAPI()

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/matches")
def get_matches():
    return {"matches": []}  # placeholder
