from fastapi import APIRouter, Query

from app.services.store import list_datasets, read_json

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("")
def available():
    return list_datasets()


@router.get("/summary")
def summary(dataset: str = Query(...)):
    return read_json(dataset, "dataset_summary.json")