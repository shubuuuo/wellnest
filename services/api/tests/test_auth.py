from app.core.security import hash_password
from app.db.models import User

BASE = "/api/v1"
NEW_USER = {"name": "Ada Lovelace", "email": "ada@gmail.com", "password": "Passw0rdX", "consent": True}


def make_admin(client):
    with client.db_factory() as db:
        db.add(User(email="boss@gmail.com", name="Boss", password_hash=hash_password("Adm1nPassX"), role="admin"))
        db.commit()


def test_register_logs_in_and_defaults_to_user_role(client):
    response = client.post(f"{BASE}/auth/register", json=NEW_USER)
    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert client.get(f"{BASE}/auth/me").json()["email"] == "ada@gmail.com"


def test_register_requires_consent_and_unique_email(client):
    assert client.post(f"{BASE}/auth/register", json={**NEW_USER, "consent": False}).status_code == 422
    assert client.post(f"{BASE}/auth/register", json=NEW_USER).status_code == 201
    assert client.post(f"{BASE}/auth/register", json=NEW_USER).status_code == 409


def test_login_rejects_wrong_password(client):
    client.post(f"{BASE}/auth/register", json=NEW_USER)
    client.post(f"{BASE}/auth/logout")
    bad = client.post(f"{BASE}/auth/login", json={"email": NEW_USER["email"], "password": "wrong-password1"})
    assert bad.status_code == 401
    good = client.post(f"{BASE}/auth/login", json={"email": NEW_USER["email"], "password": NEW_USER["password"]})
    assert good.status_code == 200


def test_protected_routes_need_login(client):
    assert client.get(f"{BASE}/auth/me").status_code == 401
    assert client.get(f"{BASE}/dataset").status_code == 401


def test_normal_user_cannot_use_admin_routes(client):
    client.post(f"{BASE}/auth/register", json=NEW_USER)
    assert client.get(f"{BASE}/admin/users").status_code == 403


def test_admin_can_manage_users_but_not_lock_themselves_out(client):
    make_admin(client)
    client.post(f"{BASE}/auth/login", json={"email": "boss@gmail.com", "password": "Adm1nPassX"})
    users = client.get(f"{BASE}/admin/users").json()
    assert users["total"] == 1
    me = users["items"][0]["id"]
    assert client.patch(f"{BASE}/admin/users/{me}", json={"role": "user"}).status_code == 409