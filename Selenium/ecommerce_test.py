"""
Flow: open homepage -> search for product -> open product -> add to cart -> go to checkout -> assert cart total.
Replace selectors and URL with the actual staging/demo env.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, traceback

def test_search_add_to_cart_checkout():
    # --- setup driver (local) ---
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")           # run headless in CI
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)       # or use webdriver_manager if you prefer

    wait = WebDriverWait(driver, 15)
    try:
        driver.get("https://staging.flipkart.example/")   # replace with staging/demo URL

        # 1) Ensure homepage search bar is visible
        search = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='q']")))
        search.clear()
        search.send_keys("smartphone")
        search.send_keys(Keys.ENTER)

        # 2) Wait for results & click first product
        first_card = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".product-card a")))
        first_card.click()

        # 3) Switch to product tab if it opens new tab/window
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # 4) Add to cart
        add_to_cart_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-to-cart")))
        add_to_cart_btn.click()

        # 5) Go to cart / checkout
        cart_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/cart']")))
        cart_btn.click()

        # 6) Assert there's at least one item in cart and extract total
        item_count = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cart-item")))
        total_elem = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".cart-total .amount")))
        total_text = total_elem.text
        assert total_text and total_text.strip() != "", "Cart total missing"

        print("PASSED: cart total:", total_text)

    except Exception:
        # Screenshot on failure (for debugging in CI)
        driver.save_screenshot("flipkart_failure.png")
        traceback.print_exc()
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    test_search_add_to_cart_checkout()
