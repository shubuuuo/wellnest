from uuid import UUID

from app.core.security import hash_password
from app.db.models import Prediction, User

BASE = "/api/v1"
ADA = {"name": "Ada Lovelace", "email": "ada@gmail.com", "password": "Passw0rdX", "consent": True}


def login_admin(client):
    with client.db_factory() as db:
        db.add(User(email="boss@gmail.com", name="Boss", password_hash=hash_password("Adm1nPassX"), role="admin"))
        db.commit()
    client.post(f"{BASE}/auth/login", json={"email": "boss@gmail.com", "password": "Adm1nPassX"})


def test_review_is_saved_cleaned_and_updated_in_place(client):
    client.post(f"{BASE}/auth/register", json=ADA)
    saved = client.put(f"{BASE}/me/review", json={"rating": 4, "comment": "  Helpful  "}).json()["review"]
    assert saved["rating"] == 4 and saved["comment"] == "Helpful"
    client.put(f"{BASE}/me/review", json={"rating": 5})
    assert client.get(f"{BASE}/me/review").json()["review"]["rating"] == 5
    assert client.put(f"{BASE}/me/review", json={"rating": 6}).status_code == 422


def test_review_needs_login(client):
    assert client.get(f"{BASE}/me/review").status_code == 401


def test_normal_user_cannot_open_admin_analytics(client):
    client.post(f"{BASE}/auth/register", json=ADA)
    for path in ("/admin/analytics", "/admin/activity", "/admin/reviews"):
        assert client.get(f"{BASE}{path}").status_code == 403


def test_admin_sees_usage_activity_and_can_remove_a_review(client):
    user_id = client.post(f"{BASE}/auth/register", json=ADA).json()["id"]
    with client.db_factory() as db:
        db.add(Prediction(user_id=UUID(user_id), dataset="lung", model_name="m", probability=0.4,
                          label=0, risk_band="moderate", inputs={}))
        db.commit()
    client.put(f"{BASE}/me/review", json={"rating": 5, "comment": "Great"})

    login_admin(client)
    data = client.get(f"{BASE}/admin/analytics?days=7").json()
    assert data["totals"]["users"] == 2 and data["totals"]["predictions"] == 1
    assert len(data["series"]) == 7
    assert data["ratings"]["count"] == 1 and data["ratings"]["average"] == 5.0
    assert data["by_dataset"][0]["dataset"] == "lung"

    actions = {i["action"] for i in client.get(f"{BASE}/admin/activity").json()["items"]}
    assert {"register", "review_created"} <= actions

    listing = client.get(f"{BASE}/admin/reviews").json()
    assert listing["total"] == 1
    assert client.delete(f"{BASE}/admin/reviews/{listing['items'][0]['id']}").status_code == 204
    assert client.get(f"{BASE}/admin/reviews").json()["total"] == 0