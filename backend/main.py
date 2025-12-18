from fastapi import FastAPI, HTTPException
from inference import predict_next_k_years, get_attribution

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/predict/{id}")
def predict(id: str, k: int = 5):
    try:
        return {
            "id": id,
            "prediction": predict_next_k_years(id, k)
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/attribution/{id}")
def attribution(id: str):
    try:
        return {
            "id": id,
            "attribution": get_attribution(id)
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))