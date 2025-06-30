import os
import time
import tempfile
import streamlit as st
import pandas as pd
from PIL import Image as PILImage
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials as admin_credentials, firestore as admin_firestore
from vertexai import init
from vertexai.generative_models import GenerativeModel, Image, Part
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service

# --- LOAD ENVIRONMENT ---
load_dotenv()
PROJECT_ID  = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

# --- INIT GOOGLE SERVICES ---
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
model = GenerativeModel("gemini-2.0-flash-001")

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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        img = PILImage.open(uploaded_file)
        img.save(tmp_file.name)
        image_path = tmp_file.name

    image_part = Part.from_image(Image.load_from_file(image_path))
    prompt = (
        "ನೀವು ಕರ್ನಾಟಕ ರೈತರಿಗೆ ಸಹಾಯ ಮಾಡಿತ್ತಿದ್ದೀರಿ. \n"
        "ಈ ಸಸ್ಯದ ಎಲೆಯ ಚಿತ್ರವನ್ನನ್ನು ನೋಡಿ. \n"
        "ದಯವಿಟ್ಟು ಕರ್ನಾಟಕದ ಹವಾಮಾನ ಮÊ4್ತು ಕೃಷಿ ಪರಿಸ್ಥಿತಿಯನ್ನ ಆಧಾರಿಸಿ, ಈ ಎಲೆಯಿಲ್ಲಿ ಕಂಡುಬರವ ರೋಗ ಅಥವಾ ಕೀಟಪೀಡೆ ಯಾವದು ಎË2್ಲಿ ಗುರುತಿಸಿ."
    )

    try:
        response = model.generate_content([prompt, image_part])
        result = response.text
        st.success("✅ Diagnosis in Kannada:")
        st.markdown(result)
        db.collection("diagnosis").add({
            "farmer": farmer_name,
            "diagnosis": result,
            "image_name": uploaded_file.name
        })
        st.info("📜 Diagnosis saved to Firebase")
    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")

st.set_page_config(page_title="🧑‍🌾 Farmer Scheme Assistant", page_icon="🌿")
st.title("🌿 Government Scheme Helper")

user_query = st.text_input("Ask about schemes (e.g., subsidies for drip irrigation):")

if user_query and st.button("Search Schemes"):
    with st.spinner("Checking government portals..."):
        prompt = (
            f"ನೀವು ಭಾರತೀಯ ರೈತರಿಗೆ арналған ಸರಕಾರೀ ಯೋಜನೆ ಸಹಾಯಕ.\n"
            f"ಸರಳ ಕನ್ನಡದಲ್ಲಿ ಉತ್ತರಿಸು. ರೈತನು ಕೇಳಿದ ಪ್ರಶ್ನೆ: {user_query}.\n"
            f"ದಯವಿಟ್ಟು ಈ ಮಾಹಿತಿ ನೀಡಿ: 1. ಯೋಜನೆಯ ಹೆಸರು 2. ಅರ್ಹತೆ 3. ಲಾಭಗಳು 4. ಅರ್ಜಿ ಹಾಕಲು ಲಿಂಕ್\n"
            f"ಕೆವಲ ಭಾರತದ ಸರಕಾರದ ಯೋಜನೆಗಳನ್ನೇ ಬಳಸಿ ಮತ್ತು ಇತ್ತೀಚಿನ 2024-2025 ಮಾಹಿತಿಯನ್ನಷ್ಟೇ ಕೊಡು."
        )

        try:
            response = model.generate_content(prompt)
            st.success("✅ Schemes Found")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"❌ Failed to fetch schemes: {e}")

global driver
global service
global wait
def scrape_agmarknet_prices(state, market, commodity):
    service = Service(r"C:\Users\prana\OneDrive\Desktop\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service)
    # driver = webdriver.Chrome()
    # driver.get("https://agmarknet.gov.in/PriceAndArrivals/CommodityPricesWeeklyReport.aspx")
    wait = WebDriverWait(driver, 20)
    driver.get("https://agmarknet.gov.in/PriceAndArrivals/CommodityPricesWeeklyReport.aspx")
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

    # Interactions
    safe_select(By.ID, "cphBody_cboState").select_by_visible_text(state)
    wait_for_min_options(By.ID, "cphBody_cboMarket", 2)
    safe_select(By.ID, "cphBody_cboMarket").select_by_visible_text(market)
    wait_for_min_options(By.ID, "cphBody_cboCommodity", 2)
    safe_select(By.ID, "cphBody_cboCommodity").select_by_visible_text(commodity)

    wait.until(EC.element_to_be_clickable((By.ID, "cphBody_btnSubmit"))).click()

    try:
        table = wait.until(EC.presence_of_element_located((By.ID, "cphBody_gridRecords")))
        rows = table.find_elements(By.TAG_NAME, "tr")

        if len(rows) <= 1:
            # Try to print the table HTML for debugging
            table_html = table.get_attribute("outerHTML") if table else "[No table element found]"
            print("[DEBUG] Table HTML when no rows found:\n", table_html)
            return pd.DataFrame()

        data = []
        for row in rows:
            cols = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            if cols:
                data.append(cols)

        # If data is not empty, try to get headers from the first row
        if data:
            headers = data[0]
            data_rows = data[1:] if len(data) > 1 else []
            df = pd.DataFrame(data_rows, columns=headers)
        else:
            df = pd.DataFrame()
        return df

    except Exception as e:
        # Print the page source for debugging
        try:
            page_html = driver.page_source
            print("[DEBUG] Page HTML on exception:\n", page_html[:2000], "... [truncated]")
        except Exception:
            print("[DEBUG] Could not get page source.")
        print(f"Error extracting table: {e}")
        return pd.DataFrame({'Error': [f'Error extracting table: {e}']})
    finally:
        driver.quit()
        

# --- STREAMLIT SCRAPER UI ---
def display_scraped_data():
    st.header("📈 Market Price Analysis for Karnataka")
    col1, col2 = st.columns(2)
    with col1:
        market = st.selectbox("Select Market", ["--", "Chintamani", "Bangarpet", "BENGALURU", "MYSORE"])
    with col2:
        commodity = st.selectbox("Select Commodity", ["--", "Potato", "Lime", "Tomato", "Rice", "Wheat"])

    if st.button("🔍 Scrape Market Prices"):
        if market == "--" or commodity == "--":
            st.warning("⚠️ Please select valid options for Market and Commodity.")
        else:
            with st.spinner("Scraping market data..."):
                df = scrape_agmarknet_prices("Karnataka", market, commodity)

                if isinstance(df, pd.DataFrame) and not df.empty:
                    st.subheader("📊 Raw Table")
                    st.dataframe(df)
                    try:
                        # Reshape for line chart
                        df_long = df.melt(id_vars="Varieties", var_name="Date", value_name="Price")
                        df_long["Date"] = pd.to_datetime(df_long["Date"], dayfirst=True, errors="coerce")
                        df_long["Price"] = pd.to_numeric(df_long["Price"].replace("NR", None), errors="coerce")
                        df_long = df_long.dropna(subset=["Date", "Price"]).sort_values("Date")
                        st.subheader("📈 Price Trend")
                        st.line_chart(df_long.set_index("Date")["Price"])
                    except Exception as e:
                        st.error(f"⚠️ Could not plot line chart: {e}")
                elif isinstance(df, pd.DataFrame) and 'Error' in df.columns:
                    st.error(df['Error'].iloc[0])
                else:
                    st.error("❌ No data found for the selected options.")


# Add the scraping section
st.markdown("---")
display_scraped_data()