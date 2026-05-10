from fastapi import FastAPI


app = FastAPI(title="Model-API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

