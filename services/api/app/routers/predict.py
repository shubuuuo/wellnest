# # import pandas as pd
# # from fastapi import APIRouter, Query
# # from pydantic import BaseModel

# # from app.core.errors import AppError
# # from app.services.store import get_best_model, get_preprocessor, read_json

# # router = APIRouter(prefix="/predict", tags=["predict"])

# # DISCLAIMER = (
# #     "This is an estimate for education only and is not a medical diagnosis. "
# #     "Please consult a qualified clinician about any health concern."
# # )


# # class PredictRequest(BaseModel):
# #     values: dict[str, float | int | str | bool]


# # @router.get("/schema")
# # def schema(dataset: str = Query(...)):
# #     return read_json(dataset, "feature_schema.json")


# # @router.post("")
# # def predict(body: PredictRequest, dataset: str = Query(...)):
# #     row = {}
# #     for field in read_json(dataset, "feature_schema.json"):
# #         raw = body.values.get(field["name"], field["default"])
# #         if field["kind"] == "number":
# #             try:
# #                 row[field["name"]] = float(raw)
# #             except (TypeError, ValueError):
# #                 raise AppError(422, "INVALID_VALUE", f"{field['name']} must be a number")
# #         else:
# #             row[field["name"]] = str(raw)

# #     frame = pd.DataFrame([row])[read_json(dataset, "columns.json")]
# #     features = get_preprocessor(dataset).transform(frame)
# #     name, model = get_best_model(dataset)
# #     probability = float(model.predict_proba(features)[0, 1])
# #     band = "low" if probability < 0.3 else "moderate" if probability < 0.7 else "high"
# #     return {
# #         "probability": round(probability, 4),
# #         "label": int(probability >= 0.5),
# #         "risk_band": band,
# #         "model": name,
# #         "disclaimer": DISCLAIMER,
# #     }

# from datetime import datetime, timezone

# import pandas as pd
# from fastapi import APIRouter, Depends, Query
# from pydantic import BaseModel
# from sqlalchemy.orm import Session

# from app.core.errors import AppError
# from app.db.models import Prediction, User
# from app.db.session import get_db
# from app.deps import get_current_user
# from app.services.store import dataset_dir, get_best_model, get_preprocessor, read_json
# from app.services.activity import log_activity

# router = APIRouter(prefix="/predict", tags=["predict"])

# DISCLAIMER = (
#     "This is an estimate for education only and is not a medical diagnosis. "
#     "Please consult a qualified clinician about any health concern."
# )


# class PredictRequest(BaseModel):
#     values: dict[str, float | int | str | bool]


# def _model_trained_at(dataset: str, model_name: str) -> datetime | None:
#     """When the model file was last written, so every saved check records which version answered."""
#     try:
#         results = read_json(dataset, "results.json")
#         entry = next(m for m in results["models"] if m["name"] == model_name)
#         modified = (dataset_dir(dataset) / entry["file"]).stat().st_mtime
#         return datetime.fromtimestamp(modified, tz=timezone.utc)
#     except (StopIteration, KeyError, OSError):
#         return None


# @router.get("/schema")
# def schema(dataset: str = Query(...)):
#     return read_json(dataset, "feature_schema.json")


# @router.post("")
# def predict(
#     body: PredictRequest,
#     dataset: str = Query(...),
#     user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     row = {}
#     for field in read_json(dataset, "feature_schema.json"):
#         raw = body.values.get(field["name"], field["default"])
#         if field["kind"] == "number":
#             try:
#                 row[field["name"]] = float(raw)
#             except (TypeError, ValueError):
#                 raise AppError(422, "INVALID_VALUE", f"{field['name']} must be a number")
#         else:
#             row[field["name"]] = str(raw)

#     frame = pd.DataFrame([row])[read_json(dataset, "columns.json")]
#     features = get_preprocessor(dataset).transform(frame)
#     name, model = get_best_model(dataset)
#     probability = round(float(model.predict_proba(features)[0, 1]), 4)
#     band = "low" if probability < 0.3 else "moderate" if probability < 0.7 else "high"

#     saved = Prediction(
#         user_id=user.id,
#         dataset=dataset,
#         model_name=name,
#         model_trained_at=_model_trained_at(dataset, name),
#         probability=probability,
#         label=int(probability >= 0.5),
#         risk_band=band,
#         inputs=row,
#     )
#     db.add(saved)
#     db.flush()
#     log_activity(db, user.id, "prediction_created", "prediction", saved.id,
#                  {"dataset": dataset, "risk_band": band})
#     db.commit()
#     db.refresh(saved)

#     return {
#         "id": str(saved.id),
#         "created_at": saved.created_at,
#         "probability": probability,
#         "label": saved.label,
#         "risk_band": band,
#         "model": name,
#         "disclaimer": DISCLAIMER,
#     }
import pandas as pd

from fastapi import APIRouter, Depends, Query

from pydantic import BaseModel

from sqlalchemy.orm import Session



from app.core.errors import AppError

from app.db.models import Prediction, User

from app.db.session import get_db

from app.deps import get_current_user

from app.services.activity import log_activity

from app.services.online import live_model

from app.services.store import get_preprocessor, read_json



router = APIRouter(prefix="/predict", tags=["predict"])



DISCLAIMER = (

    "This is an estimate for education only and is not a medical diagnosis. "

    "Please consult a qualified clinician about any health concern."

)





class PredictRequest(BaseModel):

    values: dict[str, float | int | str | bool]





@router.get("/schema")

def schema(dataset: str = Query(...)):

    return read_json(dataset, "feature_schema.json")





@router.post("")

def predict(

    body: PredictRequest,

    dataset: str = Query(...),

    user: User = Depends(get_current_user),

    db: Session = Depends(get_db),

):

    row = {}

    for field in read_json(dataset, "feature_schema.json"):

        raw = body.values.get(field["name"], field["default"])

        if field["kind"] == "number":

            try:

                row[field["name"]] = float(raw)

            except (TypeError, ValueError):

                raise AppError(422, "INVALID_VALUE", f"{field['name']} must be a number")

        else:

            row[field["name"]] = str(raw)



    frame = pd.DataFrame([row])[read_json(dataset, "columns.json")]

    features = get_preprocessor(dataset).transform(frame)

    live = live_model(db, dataset)

    probability = round(float(live.model.predict_proba(features)[0, 1]), 4)

    band = "low" if probability < 0.3 else "moderate" if probability < 0.7 else "high"



    saved = Prediction(

        user_id=user.id,

        dataset=dataset,

        model_name=live.name,

        model_trained_at=live.trained_at,  # = when this exact model version was created

        probability=probability,

        label=int(probability >= 0.5),

        risk_band=band,

        inputs=row,

    )

    db.add(saved)

    db.flush()

    log_activity(db, user.id, "prediction_created", "prediction", saved.id, {"dataset": dataset, "risk_band": band})

    db.commit()

    db.refresh(saved)



    return {

        "id": str(saved.id),

        "created_at": saved.created_at,

        "probability": probability,

        "label": saved.label,

        "risk_band": band,

        "model": f"{live.name} (v{live.version})",

        "disclaimer": DISCLAIMER,

    }