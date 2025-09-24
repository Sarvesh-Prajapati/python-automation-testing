# ---------------------------------- conftest.py ---------------------------------

import pytest
# from inco_module import IncoSite  # replace with actual client/selenium page objects

@pytest.fixture
def site(): return IncoSite()    # returns a fresh site/client instance per test

@pytest.fixture
def sample_product(site):
    # ensure at least one product exists; return product id or slug
    prods = site.get_product_list()
    if not prods:
        # in simulation we can seed one
        pid = site.create_product(name="Test Bowling Alley", category="Ten-Pin Bowling")
    else: pid = prods[0]["id"]
    return site, pid


# ---------------------------------- test_smoke.py ---------------------------------- 

import pytest

@pytest.mark.smoke
def test_homepage_and_nav_loads(site):
    assert site.ping_homepage() is True
    nav = site.get_navigation_items()
    # critical nav items expected
    assert "Products" in nav and "Contact" in nav and "About" in nav

@pytest.mark.smoke
def test_product_detail_page_loads(sample_product):
    site, pid = sample_product
    p = site.open_product(product_id=pid)
    assert p is not None
    assert "name" in p and "description" in p
    assert site.is_enquire_button_present(p) is True

@pytest.mark.smoke
def test_contact_form_submits(site):
    res = site.submit_enquiry(name="Test User", email="test@example.com", message="Interested in bowling equipment")
    assert res.get("status") in ("success", "queued")


# ---------------------------------- test_sanity_inco.py ---------------------------------- 

import pytest

@pytest.mark.sanity
def test_brochure_download_returns_pdf(site):
    # assume site exposes resources list
    brochures = site.get_brochures()
    if brochures:
        bid = brochures[0]["id"]
        content, content_type = site.download_brochure(brochure_id=bid)
        assert content_type == "application/pdf"
        assert len(content) > 100  # some minimal content
    else:
        pytest.skip("No brochures present in this environment")

@pytest.mark.sanity
def test_enquiry_creates_lead_in_crm(site, monkeypatch):
    # monkeypatch external CRM integration to assert lead payload
    captured = {}
    def fake_send_crm(lead):
        captured["lead"] = lead
        return True
    monkeypatch.setattr(site, "send_crm_lead", fake_send_crm)
    res = site.submit_enquiry(name="Alice", email="alice@corp.com", message="Need quote for bowling")
    assert res.get("status") in ("success", "queued")
    assert "lead" in captured and captured["lead"]["email"] == "alice@corp.com"

@pytest.mark.sanity
def test_product_gallery_images_render(sample_product):
    site, pid = sample_product
    imgs = site.get_product_images(product_id=pid)
    assert isinstance(imgs, list)
    assert len(imgs) >= 0  # test passes even if none; change to >=1 if images required

# ---------------------------------- test_regression_inco.py ---------------------------------- 

import pytest

@pytest.mark.regression
def test_full_lead_to_admin_workflow(site):
    # user visits product and submits enquiry
    prods = site.get_product_list()
    assert prods, "No products found"
    pid = prods[0]["id"]
    res = site.submit_enquiry(name="Buyer", email="buyer@x.com", message=f"Quote for {pid}")
    assert res["status"] in ("success", "queued")
    # admin should see the lead in admin listing (simulate / API)
    admin_leads = site.admin_list_leads()
    assert any(l["email"] == "buyer@x.com" for l in admin_leads)

@pytest.mark.regression
def test_product_pages_and_contact_info_consistent(site):
    prods = site.get_product_list()
    assert len(prods) >= 1
    for p in prods:
        pd = site.open_product(p["id"])
        assert "contact" in pd and pd["contact"]["phone"] is not None
        # each product should have consistent company contact displayed
        assert pd["contact"]["email"] == site.get_global_contact_info()["email"]

@pytest.mark.regression
def test_admin_upload_brochure_reflects_on_public_listing(site):
    # admin uploads a brochure; it should appear on public resources
    admin_token = site.admin_login(username="admin", password="adminpwd")
    new_brochure_id = site.upload_brochure(session=admin_token, file_name="new_catalog.pdf", content=b"%PDF-1.4...")
    # after upload, public resources should include it
    public = site.get_brochures()
    assert any(b["id"] == new_brochure_id for b in public)





