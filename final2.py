from fastapi import FastAPI
from typing import List, Dict
import spacy
import re
import subprocess

app = FastAPI()

# Check if en_core_web_sm is installed, and install it if not
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm model...")
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Define regular expressions for email and phone number patterns
email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}"
phone_pattern = r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"

def extract_info(text: str) -> Dict[str, List[str]]:
    doc = nlp(text)

    names = []
    emails = []
    phone_numbers = []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            names.append(ent.text)
        elif re.match(email_pattern, ent.text):
            emails.append(ent.text)
        elif re.match(phone_pattern, ent.text):
            phone_numbers.append(ent.text)

    return {
        "names": names,
        "emails": emails,
        "phone_numbers": phone_numbers
    }

@app.post("/extract-info")
def extract_info_endpoint(text: str) -> Dict[str, List[str]]:
    return extract_info(text)
