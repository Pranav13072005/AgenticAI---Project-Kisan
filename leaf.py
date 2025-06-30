import os
from vertexai import init
from vertexai.generative_models import GenerativeModel, Part


import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials as admin_credentials, firestore as admin_firestore
from vertexai.generative_models import GenerativeModel, Image, Part
import vertexai
import tempfile
from PIL import Image as PILImage
from dotenv import load_dotenv
import os


load_dotenv()

PROJECT_ID  = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")


from vertexai import init
init(project=PROJECT_ID, location=LOCATION) #initialization


SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")


credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
model = GenerativeModel("gemini-2.0-flash-001")  # safer public model

# --- INIT FIREBASE (Safe check) ---
admin_cred = admin_credentials.Certificate(SERVICE_ACCOUNT_FILE)
if not firebase_admin._apps:
    firebase_admin.initialize_app(admin_cred)

db = admin_firestore.client()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Project Kisan", page_icon="🌾")
st.title("🌾 Project Kisan – Crop Disease Detection")

farmer_name = st.text_input("👨‍🌾 Enter Farmer's Name")
uploaded_file = st.file_uploader("📷 Upload Crop Leaf Image", type=["jpg", "jpeg", "png"])

if uploaded_file and st.button("Diagnose Disease"):
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    # Save image temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        img = PILImage.open(uploaded_file)
        img.save(tmp_file.name)
        image_path = tmp_file.name

    # Prepare image part
    image_part = Part.from_image(Image.load_from_file(image_path))

    # Prompt in Kannada
    prompt = (
        "ನೀವು ಕರ್ನಾಟಕದ ರೈತರಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತಿದ್ದೀರಿ. ಈ ಸಸ್ಯದ ಎಲೆಯ ಚಿತ್ರವನ್ನು ನೋಡಿ. "
        "ದಯವಿಟ್ಟು ಕರ್ನಾಟಕದ ಹವಾಮಾನ ಮತ್ತು ಕೃಷಿ ಪರಿಸ್ಥಿತಿಯನ್ನು ಆಧರಿಸಿ, ಈ ಎಲೆಯಲ್ಲಿ ಕಂಡುಬರುವ ರೋಗ ಅಥವಾ ಕೀಟಪೀಡೆ ಯಾವದು ಎಂಬುದನ್ನು ಗುರುತಿಸಿ. "
        "ಪ್ರಸಕ್ತ ಕರ್ಣಾಟಕದ ಡೇಟಾ ಮತ್ತು ಸ್ಥಳೀಯವಾಗಿ ಸಾಮಾನ್ಯವಾಗಿರುವ ಸಮಸ್ಯೆಗಳ ಆಧಾರದಲ್ಲಿ ಮಾತ್ರ ಉತ್ತರ ನೀಡಿ. "
        "ದಯವಿಟ್ಟು ಈ ಸಮಸ್ಯೆಗೆ ಸರಳ, ರೈತರಿಗೆ ಅರ್ಥವಾಗುವಂತಹ ಕನ್ನಡದಲ್ಲಿ ಸ್ಥಳೀಯವಾಗಿ ಲಭ್ಯವಿರುವ ಪರಿಹಾರವನ್ನು ಮಾತ್ರ ನೀಡಿರಿ."
    )

    try:
        response = model.generate_content([prompt, image_part])
        result = response.text

        st.success("✅ Diagnosis in Kannada:")
        st.markdown(result)

        # Save to Firestore
        db.collection("diagnosis").add({
            "farmer": farmer_name,
            "diagnosis": result,
            "image_name": uploaded_file.name
        })

        st.info("📝 Diagnosis saved to Firebase")

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")



#------------------------------PRICE DETECTION PART (WORKING UNTIL TABLE PRINT)------------------------------
# from selenium.webdriver.chrome.service import Service
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait, Select
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import StaleElementReferenceException
# import time

# from selenium import webdriver

# service = Service(r"C:\Users\prana\OneDrive\Desktop\chromedriver-win64\chromedriver.exe")
# driver = webdriver.Chrome(service=service)
# # driver.get("https://www.google.com")

# # Initialize driver
# # driver = webdriver.Chrome()
# driver.get("https://agmarknet.gov.in/PriceAndArrivals/CommodityPricesWeeklyReport.aspx")
# wait = WebDriverWait(driver, 20)

# # --- Utility Functions ---
# def safe_select(by, locator):
#     """Try 3 times to safely wrap element in Select."""
#     for _ in range(3):
#         try:
#             element = driver.find_element(by, locator)
#             return Select(element)
#         except StaleElementReferenceException:
#             time.sleep(1)
#     raise Exception(f"Element not stable: {locator}")

# def wait_for_option(by, locator, text, timeout=20):
#     """Wait until the dropdown has a specific option."""
#     def check_option(d):
#         for _ in range(3):
#             try:
#                 select = Select(d.find_element(by, locator))
#                 return any(text.strip() == opt.text.strip() for opt in select.options)
#             except StaleElementReferenceException:
#                 time.sleep(1)
#         return False
#     WebDriverWait(driver, timeout).until(check_option)

# def wait_for_min_options(by, locator, min_count=2, timeout=20):
#     """Wait until dropdown has at least `min_count` options."""
#     def check_count(d):
#         for _ in range(3):
#             try:
#                 select = Select(d.find_element(by, locator))
#                 return len(select.options) >= min_count
#             except StaleElementReferenceException:
#                 time.sleep(1)
#         return False
#     WebDriverWait(driver, timeout).until(check_count)

# # --- Interactions ---

# # state
# safe_select(By.ID, "cphBody_cboState").select_by_visible_text("Karnataka")

# # Market
# wait_for_min_options(By.ID, "cphBody_cboMarket", 2)
# safe_select(By.ID, "cphBody_cboMarket").select_by_visible_text("Chintamani")

# # commodity
# wait_for_min_options(By.ID, "cphBody_cboCommodity", 2)
# safe_select(By.ID, "cphBody_cboCommodity").select_by_visible_text("Potato")


# # --- Submit ---
# wait.until(EC.element_to_be_clickable((By.ID, "cphBody_btnSubmit"))).click()

# # --- Extract Table ---
# try:
#     # Wait for table to load
#     table = wait.until(EC.presence_of_element_located((By.ID, "cphBody_gridRecords")))
#     rows = table.find_elements(By.TAG_NAME, "tr")

#     if len(rows) <= 1:
#         print("⚠️ No data found in the table.")
#     else:
#         for row in rows:
#             cols = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
#             if cols:
#                 print(cols)

# except Exception as e:
#     print("❌ Error extracting table:", e)

# # Clean exit
# driver.quit()


import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

# --- Streamlit UI ---
st.set_page_config(page_title="Agmarknet Prices", page_icon="🌾")
st.title("🌾 Agmarknet Crop Price Scraper")
st.markdown("Scraping market prices from [Agmarknet.gov.in](https://agmarknet.gov.in)")

# --- Selenium Setup ---
service = Service(r"C:\Users\prana\OneDrive\Desktop\chromedriver-win64\chromedriver.exe")
driver = webdriver.Chrome(service=service)
driver.get("https://agmarknet.gov.in/PriceAndArrivals/CommodityPricesWeeklyReport.aspx")
wait = WebDriverWait(driver, 20)

# --- Utility Functions ---
def safe_select(by, locator):
    for _ in range(3):
        try:
            element = driver.find_element(by, locator)
            return Select(element)
        except StaleElementReferenceException:
            time.sleep(1)
    raise Exception(f"Element not stable: {locator}")

def wait_for_min_options(by, locator, min_count=2, timeout=20):
    def check_count(d):
        for _ in range(3):
            try:
                select = Select(d.find_element(by, locator))
                return len(select.options) >= min_count
            except StaleElementReferenceException:
                time.sleep(1)
        return False
    WebDriverWait(driver, timeout).until(check_count)

# --- Scraping Process ---
try:
    safe_select(By.ID, "cphBody_cboState").select_by_visible_text("Karnataka")
    wait_for_min_options(By.ID, "cphBody_cboMarket", 2)
    safe_select(By.ID, "cphBody_cboMarket").select_by_visible_text("Chintamani")
    wait_for_min_options(By.ID, "cphBody_cboCommodity", 2)
    safe_select(By.ID, "cphBody_cboCommodity").select_by_visible_text("Potato")
    wait.until(EC.element_to_be_clickable((By.ID, "cphBody_btnSubmit"))).click()

    # --- Extract Table ---
    table = wait.until(EC.presence_of_element_located((By.ID, "cphBody_gridRecords")))
    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []

    for row in rows:
        cols = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
        if cols:
            data.append(cols)

    driver.quit()

    if len(data) <= 1:
        st.warning("⚠️ No data found in the table.")
    else:
        df = pd.DataFrame(data[1:], columns=data[0])
        st.success("✅ Data successfully scraped!")
        st.dataframe(df)

        # --- Debug Column Names ---
        st.write("🔍 Column Names:", df.columns.tolist())

        # --- Plot Line Chart ---
        # Transpose date-price columns into long format
    try:
        # Drop "Varieties" column to isolate date columns
        melted = df.melt(id_vars=["Varieties"], var_name="Date", value_name="Price")

        # Convert date and price to appropriate types
        melted["Date"] = pd.to_datetime(melted["Date"], dayfirst=True, errors="coerce")
        melted["Price"] = pd.to_numeric(melted["Price"].replace("NR", None), errors="coerce")

        # Drop missing values and sort
        melted = melted.dropna(subset=["Date", "Price"]).sort_values("Date")

        # Show line chart
        st.markdown("### 📈 Modal Price Trend")
        st.line_chart(melted.set_index("Date")["Price"])

    except Exception as e:
        st.error(f"⚠️ Could not plot line chart: {e}")

except Exception as e:
    driver.quit()
    st.error(f"❌ Error extracting table: {e}")


