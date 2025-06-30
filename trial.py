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
import vertexai
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

# Init Gemini
vertexai.init(project=PROJECT_ID, location=LOCATION)
# model = GenerativeModel("gemini-1.5-flash")  # or "gemini-1.5-pro"

