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

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests

# Page setup
st.set_page_config(page_title="Crop Market Trends", page_icon="📈")

st.title("📊 Real-time Crop Market Price Trends")
st.markdown("Get the past 7-day price trend of your crop from a selected market (Karnataka only).")

# Region & crop options
regions = {
    "Bengaluru": "BENGALURU",
    "Mysuru": "MYSORE",
    "Belagavi": "BELGAUM",
    "Dharwad": "DHARWAD",
    "Tumakuru": "TUMKUR"
}

crops = ["Tomato", "Onion", "Paddy(Dhan)(Common)", "Dry Chillies", "Turmeric"]

selected_region = st.selectbox("📍 Select Market (Region)", list(regions.keys()))
selected_crop = st.selectbox("🌾 Select Crop", crops)

# API configuration
API_KEY = "579b464db66ec23bdd00000111f6e37475da4ab1709c2a0ad6746e01"
RESOURCE_ID = "3e87c431-9c00-4a11-8d32-00bf9c6bd967"

def fetch_agmarknet_data(state, market, commodity):
    url = (
        f"https://api.data.gov.in/resource/{RESOURCE_ID}?"
        f"api-key={API_KEY}&format=json&limit=1000"
        f"&state={state}&market={market}&commodity={commodity}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        records = data.get("records", [])

        if not records:
            return None

        df = pd.DataFrame(records)
        if "arrival_date" not in df.columns or "modal_price" not in df.columns:
            return None

        df = df[["arrival_date", "modal_price"]]
        df.columns = ["Date", "Price"]
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        df.dropna(inplace=True)

        # Keep only latest 7 unique days with mean price
        df = df.groupby("Date", as_index=False).mean()
        df = df.sort_values("Date").tail(7)

        return df

    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None

# Display data
if selected_crop and selected_region:
    st.info(f"🔄 Fetching data for **{selected_crop}** in **{selected_region}**, Karnataka...")
    df = fetch_agmarknet_data("Karnataka", regions[selected_region], selected_crop)

    if df is not None and not df.empty:
        st.subheader("📈 Modal Price Trend (₹ per 100kg)")
        st.line_chart(df.set_index("Date")["Price"])

        # Price trend analysis
        start_price = df["Price"].iloc[0]
        end_price = df["Price"].iloc[-1]

        st.markdown("### 📊 Price Analysis")
        st.markdown(f"**First Day:** ₹{start_price:.2f} per 100kg (₹{start_price/100:.2f} per kg)")
        st.markdown(f"**Last Day:** ₹{end_price:.2f} per 100kg (₹{end_price/100:.2f} per kg)")

        if end_price > start_price:
            st.success("📈 Price is rising. You may consider waiting before selling.")
        elif end_price < start_price:
            st.warning("📉 Price is falling. You might want to sell soon.")
        else:
            st.info("📊 Price is stable over the past week.")
    else:
        st.error("⚠️ No recent data found for the selected crop and market.")

# import streamlit as st
# import pandas as pd
# import numpy as np
# from datetime import datetime
# import requests
# from sklearn.linear_model import LinearRegression

# # Streamlit app setup
# st.set_page_config(page_title="Project Kisan - Price Trend & Prediction", page_icon="🌾")
# st.title("🌾 Project Kisan – Live Crop Market Price Trends & Prediction")
# st.markdown("🔍 Real-time price trends, tomorrow’s prediction & selling advice for farmers in Karnataka.")

# # Dropdown options
# regions = {
#     "Bengaluru": "BENGALURU",
#     "Mysuru": "MYSORE",
#     "Belagavi": "BELGAUM",
#     "Dharwad": "DHARWAD",
#     "Tumakuru": "TUMKUR"
# }
# crops = ["Tomato", "Onion", "Paddy(Dhan)(Common)", "Dry Chillies", "Turmeric"]

# selected_region = st.selectbox("📍 Select Market", list(regions.keys()))
# selected_crop = st.selectbox("🌾 Select Crop", crops)

# # Function to fetch API data
# def fetch_agmarknet_data(market, commodity):
#     resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
#     api_key = "579b464db66ec23bdd00000111f6e37475da4ab1709c2a0ad6746e01"  # Replace this with your actual key
#     url = (
#         f"https://api.data.gov.in/resource/{resource_id}"
#         f"?api-key={api_key}&format=json&limit=1000"
#         f"&state=Karnataka&market={market}&commodity={commodity}"
#     )

#     try:
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()  # Will raise HTTPError for 403/404
#         data = response.json()
#         records = data.get("records", [])
#         if not records:
#             return None
#         df = pd.DataFrame(records)
#         df = df[["arrival_date", "modal_price"]]
#         df.columns = ["Date", "Price"]
#         df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
#         df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
#         df.dropna(inplace=True)
#         df = df.sort_values("Date", ascending=False)
#         df = df.groupby("Date").mean().reset_index().sort_values("Date")
#         return df.tail(7)
#     except requests.exceptions.HTTPError as e:
#         st.error(f"🚨 API returned an HTTP error: {e}")
#         return None
#     except Exception as e:
#         st.error(f"🚨 Other error: {e}")
#         return None
# # Price prediction logic
# def analyze_and_predict(df):
#     df = df.copy()
#     df["Day"] = np.arange(len(df))
#     model = LinearRegression()
#     model.fit(df[["Day"]], df["Price"])
#     predicted_price = model.predict([[df["Day"].max() + 1]])[0]
#     return predicted_price

# # UI Logic
# if selected_crop and selected_region:
#     st.info(f"Fetching data for *{selected_crop}* in *{selected_region}*...")
#     df = fetch_agmarknet_data(regions[selected_region], selected_crop)

#     if df is not None and not df.empty:
#         st.subheader("📈 7-Day Modal Price Trend (₹/Quintal)")
#         st.line_chart(df.set_index("Date")["Price"])

#         predicted = analyze_and_predict(df)
#         today_price = df["Price"].iloc[-1]
#         change = predicted - today_price

#         if change > 0:
#             advice = "✅ Price is likely to rise. Consider waiting."
#         elif change < 0:
#             advice = "⚠ Price may fall. Better to sell today."
#         else:
#             advice = "📊 Price looks stable. You can sell anytime."

#         st.success(f"Predicted Tomorrow's Price: ₹{predicted:.2f}")
#         st.info(f"Today's Price: ₹{today_price:.2f}")
#         st.warning(advice)
#     else:
#         st.error("⚠ No data available for this crop and market. Try a different combination.")

