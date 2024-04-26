from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import zipfile
import os
import csv
import subprocess
import re  # Added missing import
import pdfplumber  # Added missing import
import spacy  # Added missing import
from docx import Document  # Added missing import
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust origins as needed
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def get_file_paths(folder_path):
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            # Construct the full path for each file
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

def extract_text(file_path):
    # Identify file type and use appropriate library
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    else:
        # Handle unsupported file types (optional)
        return None
    return text

def extract_info(text):
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("Downloading en_core_web_sm model...")
        subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
        nlp = spacy.load("en_core_web_sm")

    doc = nlp(text)
    data = {}
    # Extract names using Named Entity Recognition (NER)
    for entity in doc.ents:
        if entity.label_ == "PERSON":
            data["name"] = entity.text
            break  # Assuming only one name per resume

    # Use regular expressions or spaCy patterns for email and phone number extraction
    email_pattern = r"[a-z0-9\.\-+_]+@[a-z0-9\-]+\.[a-z]+"
    phone_pattern = r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"
    matches = re.findall(email_pattern, text)
    if matches:
        data["email"] = matches[0]
    matches = re.findall(phone_pattern, text)
    if matches:
        data["phone_number"] = matches[0]
    return data

def get_data(file_paths):
    data = []
    for resume in file_paths:
        text = extract_text(resume)
        if text:
            info = extract_info(text)
            if info:
                data.append(info)
    return data

def generate_csv(data, fieldnames):
    with open("data.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print("Data Written Successfully")

def extract_zip(zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Extract all contents to the same directory
        zip_ref.extractall()
        # Get a list of all extracted files and folders (assuming single folder)
        extracted_items = zip_ref.namelist()
        extracted_folder = extracted_items[0]
        # Remove filename from path to get folder path
        folder_path = os.path.dirname(extracted_folder)
        return os.path.abspath(folder_path)

@app.post("/upload-zip/")
async def upload_zip_file(file: UploadFile):
    try:
        # Save the uploaded zip file
        zip_file_path = "uploaded.zip"
        with open(zip_file_path, 'wb') as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)

        # Extract the zip file
        unzipped_path = extract_zip(zip_file_path)

        # Get file paths from the extracted folder
        file_paths = get_file_paths(unzipped_path)

        # Process data and generate CSV
        data = get_data(file_paths)
        fieldnames = ["name", "email", "phone_number"]  # Define field names for CSV
        generate_csv(data, fieldnames)

        return {"message": "Data extracted and CSV generated successfully"}

    except Exception as e:
        return {"error": str(e)}
    
@app.get("/download-csv/")
async def download_csv_file():
    try:
        # Assuming the CSV file is generated in the current directory with the name "data.csv"
        csv_file_path = "data.csv"

        # Check if the CSV file exists
        if os.path.exists(csv_file_path):
            # Return the CSV file as a response
            return FileResponse(csv_file_path, media_type="text/csv", filename="data.csv")
        else:
            return {"error": "CSV file not found"}

    except Exception as e:
        return {"error": str(e)}
