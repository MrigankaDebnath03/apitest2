from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import zipfile
import os
import csv
from pyresparser import ResumeParser
from starlette.middleware.cors import CORSMiddleware
import subprocess
import nltk

# Download NLTK stopwords if not already available
nltk.download('stopwords')


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500/", "*"],  # Adjust origins as needed
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def download_spacy_model():
    """Downloads the en_core_web_sm spaCy model using subprocess."""
    command = ["python", "-m", "spacy", "download", "en_core_web_sm"]
    subprocess.run(command)


# Call the download_spacy_model function before the app starts
download_spacy_model()


def get_file_paths(folder_path):
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            # Construct the full path for each file
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths


def get_data(file_paths):
    data1 = []
    for resume in file_paths:
        data = ResumeParser(resume).get_extracted_data()
        data1.append(data)

    fieldnames = list(data1[0].keys())

    return data1, fieldnames


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

        # Get a list of all extracted files and folders
        extracted_items = zip_ref.namelist()

        # Assuming the folder is the first item (you may need to adjust this logic)
        extracted_folder = extracted_items[0]

        # Remove the filename from the path to get the folder path
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

        # Process data and generate fieldnames
        data, fieldnames = get_data(file_paths)

        # Generate the CSV file
        generate_csv(data, fieldnames)

        return {"message": "Zip uploaded and processed successfully. Download CSV at /download/data.csv"}
    except Exception as e:
        print(e)
        return {"message": "Error uploading and processing the zip file"}
    finally:
        file.file.close()


@app.get("/download/data.csv")
async def download_csv():
    # Check if data.csv exists (optional)
    if not os.path.exists("data.csv"):
        return {"message": "No data available to download. Upload a zip file first."}

    return FileResponse("data.csv", media_type="text/csv", filename="data.csv")
