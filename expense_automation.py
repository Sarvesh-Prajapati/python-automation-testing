# --------------------------- conftest.py ---------------------------
import pytest
from zento_module import ZentoApp  # simulated module (or an API wrapper)

@pytest.fixture
def app(): return ZentoApp()     # returns a fresh app instance per test

@pytest.fixture
def employee_session(app):
    token = app.login(role="employee", username="alice", password="alicepwd")
    return app, token

@pytest.fixture
def manager_session(app):
    token = app.login(role="manager", username="manager1", password="managerpwd")
    return app, token

# --------------------------- test_smoke.py ---------------------

import pytest

@pytest.mark.smoke
def test_homepage_and_login_loads(app):
    # Basic health check: site reachable and login works for employee
    assert app.ping_homepage() is True
    token = app.login(role="employee", username="alice", password="alicepwd")
    assert token and token.startswith("session_")

@pytest.mark.smoke
def test_employee_can_create_basic_claim(employee_session):
    app, token = employee_session
    # create a minimal claim (date, category, amount)
    claim_id = app.create_claim(session=token, title="Taxi to client site", amount=500.0, date="2025-09-10", category="Travel")
    assert isinstance(claim_id, int)
    status = app.get_claim_status(claim_id)
    assert status in ("Created", "Submitted")

@pytest.mark.smoke
def test_manager_dashboard_lists_pending_claims(manager_session, app):
    mgr_app, mgr_token = manager_session
    # Ensure manager can access pending claims listing
    pending = mgr_app.list_pending_claims(session=mgr_token)
    assert isinstance(pending, list)
    # critical functionality: pending list should be retrievable (even if empty)
    assert pending is not None

# --------------------------- test_sanity.py ------------------------------

import pytest

@pytest.mark.sanity
def test_receipt_upload_attaches_to_claim(employee_session):
    app, token = employee_session
    claim_id = app.create_claim(session=token, title="Lunch while travel", amount=300.0, date="2025-09-11", category="Meals")
    # upload receipt (binary or path)
    upload_ok = app.upload_receipt(session=token, claim_id=claim_id, filename="receipt1.jpg", content=b"JPEGDATA")
    assert upload_ok is True
    receipts = app.get_claim_receipts(claim_id)
    assert any(r["filename"] == "receipt1.jpg" for r in receipts)

@pytest.mark.sanity
def test_claim_amount_validation_for_perdiem(employee_session):
    app, token = employee_session
    # Suppose per-diem for Meals is 200; test system flags higher amounts
    claim_id = app.create_claim(session=token, title="Expensive meal", amount=500.0, date="2025-09-12", category="Meals")
    validation = app.validate_claim(claim_id)
    # validate_claim returns issues list; we expect at least one warning for exceeding per-diem
    assert any("per-diem" in issue.lower() or "exceed" in issue.lower() for issue in validation)

@pytest.mark.sanity
def test_manager_can_approve_claim_and_status_updates(manager_session, app, employee_session):
    app_emp, emp_token = employee_session
    claim_id = app_emp.create_claim(session=emp_token, title="Local conveyance", amount=150.0, date="2025-09-13", category="Travel")
    # Manager approves
    mgr_app, mgr_token = manager_session
    ok = mgr_app.manager_approve(session=mgr_token, claim_id=claim_id, comment="OK")
    assert ok is True
    status = app.get_claim_status(claim_id)
    assert status == "Approved"


# --------------------------- test_regression.py ------------------------------

import pytest

@pytest.mark.regression
def test_full_claim_lifecycle_finance_disbursement(employee_session, manager_session, app):
    app_emp, emp_token = employee_session
    # Employee submits claim
    claim_id = app_emp.create_claim(session=emp_token, title="Hotel stay", amount=2500.0, date="2025-09-05", category="Lodging")
    app_emp.submit_claim(session=emp_token, claim_id=claim_id)

    # Manager approves
    mgr_app, mgr_token = manager_session
    assert mgr_app.manager_approve(session=mgr_token, claim_id=claim_id, comment="Approved") is True

    # Finance processes payment
    finance_ok = app.finance_process_payment(claim_id=claim_id, payment_ref="TXN12345")
    assert finance_ok is True

    # Employee should see paid status
    status = app.get_claim_status(claim_id)
    assert status == "Paid"

@pytest.mark.regression
def test_role_based_access_control(app, employee_session, manager_session):
    app_emp, emp_token = employee_session
    # Employee tries to approve (should be rejected)
    claim_id = app_emp.create_claim(session=emp_token, title="Taxi", amount=200.0, date="2025-09-07", category="Travel")
    with pytest.raises(PermissionError):
        app_emp.manager_approve(session=emp_token, claim_id=claim_id, comment="Forged approval")

    # Manager should be able but cannot edit employee profile
    mgr_app, mgr_token = manager_session
    with pytest.raises(PermissionError):
        mgr_app.update_user_profile(session=mgr_token, username="alice", new_profile={"email":"hacker@example.com"})

@pytest.mark.regression
def test_reports_and_csv_export_correct_totals(app, employee_session):
    app_emp, emp_token = employee_session
    # Create a few claims in known amounts
    c1 = app_emp.create_claim(session=emp_token, title="Meal A", amount=100.0, date="2025-08-01", category="Meals")
    c2 = app_emp.create_claim(session=emp_token, title="Taxi A", amount=150.0, date="2025-08-02", category="Travel")
    app_emp.submit_claim(session=emp_token, claim_id=c1)
    app_emp.submit_claim(session=emp_token, claim_id=c2)
    # Manager approve both
    mgr = app.login(role="manager", username="manager1", password="managerpwd")
    app.manager_approve(session=mgr, claim_id=c1, comment="OK")
    app.manager_approve(session=mgr, claim_id=c2, comment="OK")
    # Finance mark as paid
    app.finance_process_payment(claim_id=c1, payment_ref="P1")
    app.finance_process_payment(claim_id=c2, payment_ref="P2")
    # Generate report for date range and export CSV
    rep = app.generate_expense_report(start_date="2025-08-01", end_date="2025-08-31")
    csv_data = app.export_report_csv(report_id=rep["id"])
    # Sum in CSV should equal the sum we provided (100+150)
    assert rep["total_amount"] == pytest.approx(250.0)
    assert "100.0" in csv_data and "150.0" in csv_data






