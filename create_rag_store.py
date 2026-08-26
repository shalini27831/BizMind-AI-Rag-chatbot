import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

PDF_FILE = "Detailed_Business_Knowledge_Manual_100_Pages.pdf"

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# --------------------------------------------------
# STEP 1: Create File Search Store
# --------------------------------------------------

print("Creating File Search Store...")

store_url = f"{BASE_URL}/fileSearchStores?key={API_KEY}"

store_data = {
    "displayName": "Business Knowledge Manual RAG",
    "embeddingModel": "models/gemini-embedding-2"
}

response = requests.post(
    store_url,
    headers={"Content-Type": "application/json"},
    json=store_data
)

print("Store status:", response.status_code)

if not response.ok:
    print(response.text)
    raise SystemExit()

store = response.json()

STORE_NAME = store["name"]

print("Store created:")
print(STORE_NAME)


# --------------------------------------------------
# STEP 2: Upload PDF
# --------------------------------------------------

print("\nUploading PDF...")

file_size = os.path.getsize(PDF_FILE)

upload_url = (
    f"https://generativelanguage.googleapis.com/"
    f"upload/v1beta/{STORE_NAME}:uploadToFileSearchStore"
    f"?key={API_KEY}"
)

headers = {
    "X-Goog-Upload-Protocol": "resumable",
    "X-Goog-Upload-Command": "start",
    "X-Goog-Upload-Header-Content-Length": str(file_size),
    "X-Goog-Upload-Header-Content-Type": "application/pdf",
    "Content-Type": "application/json"
}

metadata = {
    "displayName": "Detailed Business Knowledge Manual"
}

response = requests.post(
    upload_url,
    headers=headers,
    json=metadata
)

print("Upload initialization status:", response.status_code)

if not response.ok:
    print(response.text)
    raise SystemExit()


# --------------------------------------------------
# STEP 3: Get upload URL
# --------------------------------------------------

upload_location = None

for key, value in response.headers.items():
    if key.lower() == "x-goog-upload-url":
        upload_location = value
        break

if not upload_location:
    print("Could not find upload URL.")
    print(response.headers)
    raise SystemExit()

print("Upload URL received.")


# --------------------------------------------------
# STEP 4: Upload PDF data
# --------------------------------------------------

with open(PDF_FILE, "rb") as f:
    pdf_data = f.read()

upload_headers = {
    "Content-Length": str(file_size),
    "X-Goog-Upload-Offset": "0",
    "X-Goog-Upload-Command": "upload, finalize"
}

response = requests.post(
    upload_location,
    headers=upload_headers,
    data=pdf_data
)

print("PDF upload status:", response.status_code)

if not response.ok:
    print(response.text)
    raise SystemExit()

operation = response.json()

print("\nUpload accepted.")
print(operation)


# --------------------------------------------------
# STEP 5: Wait for indexing
# --------------------------------------------------

operation_name = operation.get("name")

if operation_name:

    print("\nIndexing PDF. Please wait...")

    operation_url = (
        f"{BASE_URL}/{operation_name}"
        f"?key={API_KEY}"
    )

    while True:

        response = requests.get(operation_url)

        if not response.ok:
            print(response.text)
            raise SystemExit()

        operation_status = response.json()

        if operation_status.get("done"):
            break

        print("Still indexing...")
        time.sleep(5)

print("\n===================================")
print("RAG KNOWLEDGE BASE READY!")
print("===================================")

print("File Search Store:")
print(STORE_NAME)

# Save store name for later
with open("store_name.txt", "w") as f:
    f.write(STORE_NAME)

print("\nStore name saved to store_name.txt")