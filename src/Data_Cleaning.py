import os
import glob
import logging
import re
import json
from datetime import datetime
import requests



def setup_logging(logs_dir="logs"):
    """
    Set up logging to file with timestamped filename.
    """
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"Data_Cleaning_{timestamp}.log")

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

def load_latest_parsed_data(data_dir="data", top_n=3):
    """
    Finds the latest parsed_data_*.json in data_dir,
    loads it, and returns its first top_n skills (or [] if not available).
    """
    os.makedirs(data_dir, exist_ok=True)
    pattern = os.path.join(data_dir, "parsed_data_*.json")
    files = glob.glob(pattern)
    if not files:
        logging.error(f"No parsed data files found in {data_dir}; please run parsing first.")
        return []

    latest_file = max(files, key=os.path.getmtime)
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_skills = data.get("skills", [])
        if not isinstance(all_skills, list):
            logging.warning(f"Expected 'skills' to be a list, got {type(all_skills)}. Returning empty.")
            return []
        # Return only the first top_n skills
        top_skills = all_skills[:top_n]
        logging.info(f"Loaded top {len(top_skills)} skills from: {latest_file}")
        return top_skills

    except Exception as e:
        logging.error(f"Failed to load parsed data: {e}")
        return []

def save_parsed_data(parsed_data, data_dir=None):
    """
    Save parsed data as a timestamped JSON file under data_dir (or ./data by default).
    Returns the full path of the saved file, or None on error.
    """
    if data_dir is None:
        data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(data_dir, f"parsed_data_{ts}.json")

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Parsed data saved to: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Failed to save parsed data: {e}")
        return None


def main():
    # Kick off logging and (optionally) capture a timestamp for other uses
    setup_logging()

    # Load the most recent parsed data
    data = load_latest_parsed_data()
    if data is None:
        logging.error("No parsed data loaded; exiting.")
        return

    # Save (or re-save) the loaded data
    saved_file = save_parsed_data(data)
    if saved_file:
        logging.info(f"Parsed data re-saved to: {saved_file}")
    else:
        logging.error("Failed to save parsed data.")



if __name__ == "__main__":
    main()
