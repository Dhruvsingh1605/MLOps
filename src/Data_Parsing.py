import argparse
import os
import re
import json
import logging
from datetime import datetime

from pdfminer.high_level import extract_text as extract_text_from_pdf
import docx


def setup_logging():
    """
    Set up logging to file with timestamped filename.
    """
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"execution_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    logging.info(f"Logging initialized. Log file: {log_filename}")
    return timestamp


def extract_text(filepath):
    """
    Extract text from PDF or DOCX file.
    """
    logging.info(f"Extracting text from: {filepath}")
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    text = ""
    try:
        if ext == ".pdf":
            text = extract_text_from_pdf(filepath)
        elif ext in [".docx", ".doc"]:
            doc = docx.Document(filepath)
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        logging.info("Text extraction successful.")
    except Exception as e:
        logging.error(f"Failed to extract text: {e}")
    return text


def parse_email_phone(text):
    """
    Parse email addresses and phone numbers from text.
    """
    logging.info("Parsing email and phone.")
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_pattern = r"\+?\d[\d\s\-()]{7,}\d"

    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    emails = list(set(emails))
    phones = list(set(phones))

    logging.info(f"Found emails: {emails}")
    logging.info(f"Found phones: {phones}")

    return emails, phones


def parse_name(text):
    """
    Heuristic: assume the first non-empty line is the candidate's name.
    """
    logging.info("Parsing name.")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else ""
    logging.info(f"Assumed name: {name}")
    return name


def parse_skills(text):
    """
    Extract skills under 'Skills' or 'Technical Skills' section.
    """
    logging.info("Parsing skills section.")
    skills = []
    pattern = re.compile(r"(?:Skills|Technical Skills)[:\n](.*?)(?:\n\n|$)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    if match:
        skills_text = match.group(1)
        # Split by comma or newline
        skills = [s.strip() for s in re.split('[,\n]', skills_text) if s.strip()]
    logging.info(f"Extracted skills: {skills}")
    return skills


def save_parsed_data(parsed_data, timestamp):
    """
    Save parsed data to JSON file with timestamp.
    """
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)
    filename = os.path.join(data_dir, f"parsed_data_{timestamp}.json")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, indent=4)
        logging.info(f"Parsed data saved to: {filename}")
    except Exception as e:
        logging.error(f"Failed to save parsed data: {e}")
    return filename


def main():
    parser = argparse.ArgumentParser(description="Resume Data Parser")
    parser.add_argument("--resume", required=True, help="/media/dhruv/Local Disk/MLops/MLOps/Data_Souce/Dhruv_resume.pdf")
    args = parser.parse_args()

    timestamp = setup_logging()
    text = extract_text(args.resume)

    name = parse_name(text)
    emails, phones = parse_email_phone(text)
    skills = parse_skills(text)

    parsed = {
        "name": name,
        "emails": emails,
        "phones": phones,
        "skills": skills,
        "source": os.path.abspath(args.resume),
        "parsed_at": datetime.now().isoformat()
    }

    save_parsed_data(parsed, timestamp)
    logging.info("Data parsing completed.")

if __name__ == "__main__":
    main()
