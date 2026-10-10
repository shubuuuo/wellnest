# # from fastapi import APIRouter, Query

# # from app.services.store import read_json

# # router = APIRouter(prefix="/models", tags=["models"])


# # @router.get("/results")
# # def results(dataset: str = Query(...)):
# #     return read_json(dataset, "results.json")

# from pydantic import BaseModel

# from app.services.retrain import retrain
# from app.services.store import read_json

# from fastapi import APIRouter, Depends, Query
# from app.deps import require_admin


# router = APIRouter(prefix="/models", tags=["models"])

# @router.post("/retrain", dependencies=[Depends(require_admin)])

# class RetrainRequest(BaseModel):
#     name: str
#     value: float | None = None


# @router.get("/results")
# def results(dataset: str = Query(...)):
#     return read_json(dataset, "results.json")


# @router.post("/retrain")
# def retrain_model(body: RetrainRequest, dataset: str = Query(...)):
#     return retrain(dataset, body.name, body.value)

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import require_admin
from app.services.retrain import retrain
from app.services.store import read_json

router = APIRouter(prefix="/models", tags=["models"])


class RetrainRequest(BaseModel):
    name: str
    value: float | None = None


@router.get("/results")
def results(dataset: str = Query(...)):
    return read_json(dataset, "results.json")


@router.post("/retrain", dependencies=[Depends(require_admin)])
def retrain_model(body: RetrainRequest, dataset: str = Query(...)):
    return retrain(dataset, body.name, body.value)