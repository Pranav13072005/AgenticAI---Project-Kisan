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
init(project=PROJECT_ID, location=LOCATION)


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
        "ನೀವು ಈ ರೈತಿಗೆ ಸಹಾಯ ಮಾಡುತ್ತಿದ್ದೀರಿ. ಈ ಸಸ್ಯದ ಎಲೆಯ ಚಿತ್ರವನ್ನು ನೋಡಿ. "
        "ಈ ಎಲೆಯಲ್ಲಿ ಯಾವ ರೋಗ ಅಥವಾ ಕೀಟಪೀಡೆ ಇದೆ ಎಂಬುದನ್ನು ಗುರುತಿಸಿ. "
        "ದಯವಿಟ್ಟು ಸರಳ ಕನ್ನಡದಲ್ಲಿ ಪರಿಹಾರವನ್ನು ನೀಡಿರಿ."
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