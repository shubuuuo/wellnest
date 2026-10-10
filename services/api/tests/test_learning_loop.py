from uuid import UUID

import pytest

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import Prediction, User
from app.services.store import list_datasets, read_json

BASE = "/api/v1"
needs_data = pytest.mark.skipif(not list_datasets(), reason="no trained dataset in ml/artifacts")


@pytest.fixture(autouse=True)
def learning_on(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "online_learning_enabled", True)
    monkeypatch.setattr(s, "online_batch_size", 1)


def person(email, training):
    return {"name": "Ada Lovelace", "email": email, "password": "Passw0rdX", "consent": True, "training_consent": training}


def new_check(client, user_id):
    ds = list_datasets()[0]["id"]
    inputs = {f["name"]: f["default"] for f in read_json(ds, "feature_schema.json")}
    with client.db_factory() as db:
        p = Prediction(user_id=UUID(user_id), dataset=ds, model_name="m", probability=0.4,
                       label=0, risk_band="moderate", inputs=inputs)
        db.add(p)
        db.commit()
        return str(p.id), ds


def login_admin(client):
    with client.db_factory() as db:
        db.add(User(email="boss@gmail.com", name="Boss", password_hash=hash_password("Adm1nPassX"), role="admin"))
        db.commit()
    client.post(f"{BASE}/auth/login", json={"email": "boss@gmail.com", "password": "Adm1nPassX"})


def test_user_can_change_training_consent(client):
    assert client.post(f"{BASE}/auth/register", json=person("ada@gmail.com", False)).json()["training_consent"] is False
    assert client.put(f"{BASE}/me/training-consent", json={"granted": True}).json()["training_consent"] is True
    assert client.get(f"{BASE}/auth/me").json()["training_consent"] is True


def test_normal_user_cannot_use_live_learning_routes(client):
    client.post(f"{BASE}/auth/register", json=person("ada@gmail.com", True))
    assert client.get(f"{BASE}/admin/outcomes").status_code == 403
    assert client.get(f"{BASE}/admin/learning/status?dataset=x").status_code == 403
    assert client.post(f"{BASE}/admin/learning/rollback?dataset=x").status_code == 403


@needs_data
def test_without_consent_nothing_enters_the_pool(client):
    uid = client.post(f"{BASE}/auth/register", json=person("ada@gmail.com", False)).json()["id"]
    check, ds = new_check(client, uid)
    login_admin(client)
    res = client.post(f"{BASE}/admin/predictions/{check}/outcome", json={"confirmed_cancer": True}).json()
    assert res["entered_pool"] is False and "update" not in res
    assert client.get(f"{BASE}/admin/learning/status?dataset={ds}").json()["pool"]["total"] == 0


@needs_data
def test_consented_check_updates_models_then_rolls_back(client):
    uid = client.post(f"{BASE}/auth/register", json=person("ada@gmail.com", True)).json()["id"]
    check, ds = new_check(client, uid)
    login_admin(client)

    res = client.post(f"{BASE}/admin/predictions/{check}/outcome", json={"confirmed_cancer": False})
    assert res.status_code == 200
    body = res.json()
    assert body["entered_pool"] is True and "update" in body
    assert client.post(f"{BASE}/admin/predictions/{check}/outcome", json={"confirmed_cancer": True}).status_code == 409

    status = client.get(f"{BASE}/admin/learning/status?dataset={ds}").json()
    assert status["pool"]["total"] == 1 and status["pool"]["waiting"] == 0
    assert status["live"]["name"]
    events = client.get(f"{BASE}/admin/learning/events?dataset={ds}").json()["items"]
    assert events[0]["kind"] == "online_update"

    rollback = client.post(f"{BASE}/admin/learning/rollback?dataset={ds}")
    assert rollback.status_code == (200 if body["update"]["accepted"] else 409)