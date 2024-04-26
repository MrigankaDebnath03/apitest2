import spacy
import re
import subprocess

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

def extract_info(text):
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

    return names, emails, phone_numbers

# Example usage
text_to_process = """
John Doe is a software engineer. You can reach him at john.doe@example.com or call him at +1 (123) 456-7890.
Jane Smith is a data scientist. Her email is jane.smith@email.com and her phone number is 987-654-3210.
"""

extracted_names, extracted_emails, extracted_phone_numbers = extract_info(text_to_process)

print("Extracted Names:", extracted_names)
print("Extracted Emails:", extracted_emails)
print("Extracted Phone Numbers:", extracted_phone_numbers)
