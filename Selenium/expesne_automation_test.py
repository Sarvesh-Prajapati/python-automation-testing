"""
Flow: login as employee -> create a new expense claim -> upload a receipt -> verify claim status/listing.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os, traceback

def test_create_claim_and_upload_receipt():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    # Store sensitive data in env vars
    base_url = os.getenv("ZENTO_BASE", "https://staging.zento.example")
    username = os.getenv("ZENTO_EMP_USER", "alice")
    password = os.getenv("ZENTO_EMP_PASS", "alicepwd")
    try:
        driver.get(f"{base_url}/login")

        # 1) Login
        wait.until(EC.visibility_of_element_located((By.NAME, "username"))).send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # 2) Navigate to "Create Claim"
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Create Claim"))).click()
        # Fill form (fields may vary)
        wait.until(EC.visibility_of_element_located((By.NAME, "title"))).send_keys("Taxi to client site")
        driver.find_element(By.NAME, "amount").send_keys("450")
        driver.find_element(By.NAME, "date").send_keys("2025-09-13")
        driver.find_element(By.NAME, "category").send_keys("Travel")

        # 3) Upload receipt. Many apps have <input type="file"> for upload
        receipt_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        # Use a small test file present in CI workspace. In local runs create this file.
        test_receipt_path = os.getenv("TEST_RECEIPT_PATH", "/tmp/test_receipt.jpg")
        receipt_input.send_keys(test_receipt_path)

        # 4) Submit claim
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # 5) Verify claim appears in "My Claims" or the newly created claim page
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "My Claims"))).click()
        # Look for claim title
        claim = wait.until(EC.visibility_of_element_located((By.XPATH, "//td[contains(text(),'Taxi to client site')]")))
        assert claim is not None
        print("PASSED: claim created and visible in My Claims")

    except Exception:
        driver.save_screenshot("zento_failure.png")
        traceback.print_exc()
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    test_create_claim_and_upload_receipt()
