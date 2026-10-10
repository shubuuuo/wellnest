import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Prediction, User
from app.services.store import list_datasets

BASE = "/api/v1"
ADA = {"name": "Ada Lovelace", "email": "ada@gmail.com", "password": "Passw0rdX", "consent": True}
BOB = {"name": "Bob Stone", "email": "bob@gmail.com", "password": "Passw0rdX", "consent": True}
ADMIN_LOGIN = {"email": "boss@gmail.com", "password": "Adm1nPassX"}


def sign_up(client, person):
    client.post(f"{BASE}/auth/logout")
    assert client.post(f"{BASE}/auth/register", json=person).status_code == 201


def make_admin(client):
    with client.db_factory() as db:
        db.add(User(email="boss@gmail.com", name="Boss", password_hash=hash_password("Adm1nPassX"), role="admin"))
        db.commit()


def add_prediction(client, email, probability=0.42, band="moderate", dataset="lung"):
    with client.db_factory() as db:
        owner = db.scalar(select(User).where(User.email == email))
        row = Prediction(user_id=owner.id, dataset=dataset, model_name="Test Model", probability=probability,
                         label=int(probability >= 0.5), risk_band=band, inputs={"age": 61.0, "gender": "Male"})
        db.add(row)
        db.commit()
        return str(row.id)


def test_history_and_summary_only_show_my_own_checks(client):
    sign_up(client, ADA)
    add_prediction(client, ADA["email"], 0.30, "moderate")
    add_prediction(client, ADA["email"], 0.55, "moderate")
    sign_up(client, BOB)
    add_prediction(client, BOB["email"], 0.9, "high")

    mine = client.get(f"{BASE}/me/predictions").json()
    assert mine["total"] == 1 and mine["items"][0]["risk_band"] == "high"

    sign_up(client, {**ADA, "email": "ada2@gmail.com"})
    assert client.get(f"{BASE}/me/summary").json()["total_checks"] == 0

    client.post(f"{BASE}/auth/logout")
    client.post(f"{BASE}/auth/login", json={"email": ADA["email"], "password": ADA["password"]})
    summary = client.get(f"{BASE}/me/summary").json()
    assert summary["total_checks"] == 2
    assert summary["datasets"][0]["trend"] == "up"  # 30% then 55%


def test_pdf_reports_download_and_belong_to_their_owner(client):
    sign_up(client, ADA)
    ada_check = add_prediction(client, ADA["email"])

    one = client.get(f"{BASE}/me/predictions/{ada_check}/report.pdf")
    assert one.status_code == 200 and one.headers["content-type"] == "application/pdf"
    assert one.content.startswith(b"%PDF")
    full = client.get(f"{BASE}/me/report.pdf")
    assert full.status_code == 200 and full.content.startswith(b"%PDF")

    sign_up(client, BOB)
    assert client.get(f"{BASE}/me/predictions/{ada_check}/report.pdf").status_code == 404


def test_history_needs_login(client):
    assert client.get(f"{BASE}/me/predictions").status_code == 401
    assert client.get(f"{BASE}/me/report.pdf").status_code == 401


def test_normal_user_cannot_use_admin_data_routes(client):
    sign_up(client, ADA)
    assert client.get(f"{BASE}/admin/predictions").status_code == 403
    assert client.get(f"{BASE}/admin/predictions/export.csv").status_code == 403


def test_admin_can_browse_filter_export_and_download(client):
    sign_up(client, ADA)
    add_prediction(client, ADA["email"], 0.30, "moderate")
    sign_up(client, BOB)
    bob_check = add_prediction(client, BOB["email"], 0.9, "high")
    with client.db_factory() as db:
        bob_id = str(db.scalar(select(User.id).where(User.email == BOB["email"])))

    make_admin(client)
    client.post(f"{BASE}/auth/logout")
    client.post(f"{BASE}/auth/login", json=ADMIN_LOGIN)

    everything = client.get(f"{BASE}/admin/predictions").json()
    assert everything["total"] == 2
    assert client.get(f"{BASE}/admin/predictions?band=high").json()["total"] == 1
    assert client.get(f"{BASE}/admin/predictions?search=ada").json()["total"] == 1
    assert client.get(f"{BASE}/admin/predictions?dataset=breast").json()["total"] == 0

    csv_file = client.get(f"{BASE}/admin/predictions/export.csv?dataset=lung")
    assert csv_file.status_code == 200 and "text/csv" in csv_file.headers["content-type"]
    lines = csv_file.text.lstrip("\ufeff").splitlines()
    assert lines[0].startswith("prediction_id,created_at,user_email") and "age" in lines[0] and len(lines) == 3

    assert client.get(f"{BASE}/admin/predictions/{bob_check}/report.pdf").content.startswith(b"%PDF")
    assert client.get(f"{BASE}/admin/users/{bob_id}/report.pdf").content.startswith(b"%PDF")
    assert client.get(f"{BASE}/admin/users/{bob_id}/summary").json()["total_checks"] == 1
    assert client.get(f"{BASE}/admin/users/{bob_id}/predictions").json()["total"] == 1


def test_csv_export_neutralises_spreadsheet_formulas(client):
    sign_up(client, {**ADA, "name": "=HYPERLINK(1)"})
    add_prediction(client, ADA["email"])
    make_admin(client)
    client.post(f"{BASE}/auth/logout")
    client.post(f"{BASE}/auth/login", json=ADMIN_LOGIN)
    text = client.get(f"{BASE}/admin/predictions/export.csv").text
    assert ",'=HYPERLINK(1)," in text


@pytest.mark.skipif(not list_datasets(), reason="no trained dataset in ml/artifacts")
def test_prediction_is_saved_with_its_inputs(client):
    sign_up(client, ADA)
    dataset = list_datasets()[0]["id"]
    result = client.post(f"{BASE}/predict?dataset={dataset}", json={"values": {}})
    assert result.status_code == 200
    saved_id = result.json()["id"]

    history = client.get(f"{BASE}/me/predictions").json()
    assert history["total"] == 1 and history["items"][0]["id"] == saved_id
    assert history["items"][0]["inputs"]  # the values used were stored
    assert client.get(f"{BASE}/me/predictions/{saved_id}/report.pdf").content.startswith(b"%PDF")