# --------------------- CREATE A ECOMMERCE SIMULATION AND TESTS; THEN RUN pytest -----------------------

import os, sys, subprocess, textwrap
project_dir = "/mnt/data/ecom_demo"
if os.path.exists(project_dir):
    # remove previous to keep clean
    import shutil
    shutil.rmtree(project_dir)
os.makedirs(project_dir, exist_ok=True)

# -------------------------------- Write minimal ecom_module --------------------------------
ecom_module = textwrap.dedent(r'''
    class PaymentError(Exception):
        pass

    class ECommerceSite:
        def __init__(self):
            self.items = {
                1: {"name":"Smartphone X Pro","price":15000.0,"stock":10},
                2: {"name":"Wireless Earbuds","price":1500.0,"stock":0},
                3: {"name":"Laptop Alpha","price":55000.0,"stock":5},
                4: {"name":"Coffee Maker","price":3500.0,"stock":3},
                5: {"name":"Phone Cover - Blue","price":299.0,"stock":100},
            }
            self.users = {"alice":"alicepwd"}
            self._session_seq = 0
            self.sessions = {}
            self._order_seq = 0
            self.orders = {}
            self.coupons = {"FLAT50": lambda t:max(t-50,0), "PERC10": lambda t:t*0.9 if t>=1000 else t}
            import payment_gateway as pg
            self.payment_gateway = pg

        def load_homepage(self): return True

        def login(self, username, password):
            if username in self.users and self.users[username]==password:
                self._session_seq += 1
                token = f"session_{self._session_seq}"
                self.sessions[token] = {"user":username, "cart":{}, "orders": []}
                return token
            raise ValueError("Invalid credentials")

        def search(self, query):
            q = query.lower()
            return [{"id":i, **m} for i,m in self.items.items() if q in m["name"].lower()]

        def add_to_cart(self, session, item_id, qty=1):
            if session not in self.sessions: raise ValueError("Invalid session")
            if item_id not in self.items: raise ValueError("Invalid item")
            if self.items[item_id]["stock"] < qty: raise ValueError("Not enough stock")
            cart = self.sessions[session]["cart"]
            cart[item_id] = cart.get(item_id,0) + qty

        def cart_total(self, session):
            cart = self.sessions[session]["cart"]
            return sum(self.items[i]["price"]*q for i,q in cart.items())

        def apply_coupon(self, session, code):
            if code not in self.coupons: raise ValueError("Invalid coupon")
            total = self.cart_total(session)
            self.sessions[session]["last_coupon"] = code
            return self.coupons[code](total)

        def checkout(self, session, payment_details):
            if session not in self.sessions: raise ValueError("Invalid session")
            cart = self.sessions[session]["cart"]
            if not cart: raise ValueError("Cart empty")
            total = self.cart_total(session)
            if "last_coupon" in self.sessions[session]:
                total = self.coupons[self.sessions[session]["last_coupon"]](total)
            success = self.payment_gateway.process(payment_details, amount=total)
            if not success: raise PaymentError("Payment failed")
            self._order_seq += 1
            order_id = self._order_seq
            self.orders[order_id] = {"id":order_id, "items":cart.copy(), "total":total, "status":"Confirmed"}
            # reduce stock and empty cart
            for iid, q in cart.items(): self.items[iid]["stock"] -= q
            self.sessions[session]["cart"] = {}
            self.sessions[session]["orders"].append(order_id)
            return order_id

        def cancel_order(self, order_id):
            if order_id not in self.orders: raise ValueError("Invalid order")
            order = self.orders[order_id]
            if order["status"] == "Cancelled": return False
            for iid,q in order["items"].items(): self.items[iid]["stock"] += q
            order["status"] = "Cancelled"
            return True

        def get_order_status(self, order_id):
            return self.orders.get(order_id, {}).get("status", "Unknown")
''')
with open(os.path.join(project_dir, "ecom_module.py"), "w") as f:
    f.write(ecom_module)

# -------------------------------- Payment_gateway stub ---------------------------------------

payment_gateway = textwrap.dedent(r'''
def process(payment_details, amount):
    card = payment_details.get("card_number","")
    return card.startswith("4111")
''')
with open(os.path.join(project_dir, "payment_gateway.py"), "w") as f:
    f.write(payment_gateway)

# -------------------------------- conftest & fixture setup-------------------------------
conftest = textwrap.dedent(r'''
import pytest
from ecom_module import ECommerceSite

@pytest.fixture
def site(): return ECommerceSite()

@pytest.fixture
def logged_in(site):
    token = site.login("alice","alicepwd")
    return site, token
''')
with open(os.path.join(project_dir, "conftest.py"), "w") as f:
    f.write(conftest)

# ------------------------ tests: SMOKE, SANITY, REGRESSION ---------------------

# ----- SMOKE

test_smoke = textwrap.dedent(r'''
import pytest

@pytest.mark.smoke
def test_homepage_loads(site): assert site.load_homepage() is True

@pytest.mark.smoke
def test_login_valid_credentials(site):
    token = site.login("alice","alicepwd")
    assert token.startswith("session_")

@pytest.mark.smoke
def test_search_returns_results(site):
    results = site.search("smartphone")
    assert any("Smartphone" in r["name"] for r in results)
''')
with open(os.path.join(project_dir, "test_smoke.py"), "w") as f:
    f.write(test_smoke)

# ----- SANITY

test_sanity = textwrap.dedent(r'''
import pytest

@pytest.mark.sanity
def test_add_item_updates_cart_total(logged_in):
    site, token = logged_in
    site.add_to_cart(token, 1, qty=2)
    assert site.cart_total(token) == pytest.approx(30000.0)

@pytest.mark.sanity
def test_apply_valid_coupon_reduces_price(logged_in):
    site, token = logged_in
    site.add_to_cart(token, 5, qty=4)  # 4*299 = 1196
    new_total = site.apply_coupon(token, "PERC10")
    assert new_total == pytest.approx(1196.0 * 0.9)

@pytest.mark.sanity
def test_checkout_creates_order_and_clears_cart(logged_in):
    site, token = logged_in
    site.add_to_cart(token, 4, qty=1)
    order_id = site.checkout(token, {"card_number":"4111222233334444"})
    assert site.get_order_status(order_id) == "Confirmed"
    assert site.cart_total(token) == 0
''')
with open(os.path.join(project_dir, "test_sanity.py"), "w") as f:
    f.write(test_sanity)

# ----- REGRESSION

test_regression = textwrap.dedent(r'''
import pytest

@pytest.mark.regression
def test_search_excludes_out_of_stock(site):
    results = site.search("earbuds")
    assert any(r["id"]==2 for r in results)
    instock = [r for r in results if r["stock"]>0]
    assert len(instock) == 0

@pytest.mark.regression
def test_cart_persistence_within_session(logged_in):
    site, token = logged_in
    site.add_to_cart(token, 1, qty=1)
    assert site.cart_total(token) == pytest.approx(15000.0)
    site.add_to_cart(token, 5, qty=2)
    assert site.cart_total(token) == pytest.approx(15000.0 + 2*299.0)

@pytest.mark.regression
def test_order_cancellation_restocks_items(logged_in):
    site, token = logged_in
    site.add_to_cart(token, 3, qty=1)
    order_id = site.checkout(token, {"card_number":"4111000099990000"})
    assert site.get_order_status(order_id) == "Confirmed"
    assert site.items[3]["stock"] == 4
    cancelled = site.cancel_order(order_id)
    assert cancelled is True
    assert site.items[3]["stock"] == 5
''')
with open(os.path.join(project_dir, "test_regression.py"), "w") as f:
    f.write(test_regression)



# Run pytest
print("Running pytest in:", project_dir)
try:
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", project_dir], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, timeout=60)
    print(result.stdout)
    print("Exit code:", result.returncode)
except Exception as e:
    print("Pytest run failed:", e)
    print("Traceback:")
    import traceback
    traceback.print_exc()

print("\nFiles created:")
for fn in sorted(os.listdir(project_dir)):
    print(" -", fn)

