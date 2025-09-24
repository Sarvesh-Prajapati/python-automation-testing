"""
Flow: open a product page -> assert product title & gallery -> submit enquiry form -> verify success message.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback, os

def test_product_enquiry_flow():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 12)
    try:
        driver.get("https://inco.in/")   # public Inco website

        # 1) Navigate to Products (example)
        products_nav = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Products")))
        products_nav.click()

        # 2) Open a specific product (e.g., Ten Pin Bowling). Adjust the link text to actual site link.
        product_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Bowling")))
        product_link.click()

        # 3) Verify product title present and gallery thumbnails exist
        title = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.product-title")))
        assert title.text.strip() != ""
        thumbs = driver.find_elements(By.CSS_SELECTOR, ".product-gallery img")
        # We expect at least one thumbnail; if not present, test purposefully checks presence
        assert len(thumbs) >= 1

        # 4) Fill Enquire form — usually a contact form on product page
        # Scroll into view or click the Enquire button that opens modal
        enquire_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.enquire-now, button.enquire-now")))
        enquire_btn.click()

        # Fill modal / form fields (selectors will vary)
        wait.until(EC.visibility_of_element_located((By.NAME, "name"))).send_keys("QA Tester")
        driver.find_element(By.NAME, "email").send_keys("tester@example.com")
        driver.find_element(By.NAME, "phone").send_keys("9999999999")
        driver.find_element(By.NAME, "message").send_keys("Requesting technical specs and quote for bowling equipment.")
        driver.find_element(By.CSS_SELECTOR, "button.submit-enquiry").click()

        # 5) Assert success message or thank-you page
        success = wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Thank') or contains(text(),'success')]")))
        assert success is not None
        print("PASSED: enquiry submitted")

    except Exception:
        driver.save_screenshot("inco_failure.png")
        traceback.print_exc()
        raise
    finally:
        driver.quit()

if __name__ == "__main__":
    test_product_enquiry_flow()
