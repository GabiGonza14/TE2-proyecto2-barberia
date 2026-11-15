from fastapi import FastAPI

app = FastAPI(title="BarberBook API")


@app.get("/health", status_code=200)
def health() -> dict[str, str]:
    return {"status": "ok"}
