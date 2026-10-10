from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Review, User
from app.db.session import get_db
from app.deps import get_current_user
from app.services.activity import log_activity
from app.schemas.auth import UserOut

router = APIRouter(prefix="/me", tags=["feedback"])


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def tidy(cls, value: str | None) -> str | None:
        return (value or "").strip() or None


def _out(r: Review) -> dict:
    return {"rating": r.rating, "comment": r.comment, "created_at": r.created_at, "updated_at": r.updated_at}


@router.get("/review")
def my_review(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.scalar(select(Review).where(Review.user_id == user.id))
    return {"review": _out(r) if r else None}


@router.put("/review")
def save_review(body: ReviewIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.scalar(select(Review).where(Review.user_id == user.id))
    if r is None:
        r = Review(user_id=user.id, rating=body.rating, comment=body.comment)
        db.add(r)
        action = "review_created"
    else:
        r.rating, r.comment = body.rating, body.comment
        action = "review_updated"
    try:
        db.flush()
        log_activity(db, user.id, action, "review", r.id, {"rating": body.rating})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "REVIEW_CONFLICT", "Please try saving again.")
    db.refresh(r)
    return {"review": _out(r)}

class TrainingConsentIn(BaseModel):
    granted: bool


@router.put("/training-consent", response_model=UserOut)
def set_training_consent(body: TrainingConsentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.granted != user.training_consent:
        user.training_consent = body.granted
        log_activity(db, user.id, "training_consent_granted" if body.granted else "training_consent_withdrawn", "user", user.id)
    db.commit()
    return user