import argparse
import os
import re
import json
import glob
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

def setup_logging(logs_dir="logs"):
    """
    Set up logging to file with timestamped filename.
    """
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"Job_Search_{timestamp}.log")

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


def load_latest_parsed_data(data_dir="data"):
    """
    Find and load the most recent parsed_data_<timestamp>.json in data_dir.
    Returns tuple (parsed_data, timestamp) or (None, None) if not found.
    """
    os.makedirs(data_dir, exist_ok=True)
    pattern = os.path.join(data_dir, "parsed_data_*.json")
    files = glob.glob(pattern)
    if not files:
        logging.error(f"No parsed data files found in {data_dir}; please run parsing first.")
        return None, None
    latest_file = max(files, key=os.path.getmtime)
    match = re.search(r'parsed_data_(\d{8}_\d{6})\.json', os.path.basename(latest_file))
    timestamp = match.group(1) if match else datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"Loaded parsed data from: {latest_file}")
        return data, timestamp
    except Exception as e:
        logging.error(f"Failed to load parsed data: {e}")
        return None, None


def construct_job_urls(skills):
    """
    Construct search URLs for job boards based on skills.
    """
    base_urls = {
        'indeed': 'https://www.indeed.com/jobs?q={query}&l=',
        'monster': 'https://www.monster.com/jobs/search/?q={query}&where=',
        'simplyhired': 'https://www.simplyhired.com/search?q={query}&l='
    }
    urls = []
    for skill in skills:
        q = "+".join(skill.split())
        for site, template in base_urls.items():
            urls.append((site, template.format(query=q)))
    logging.info(f"Constructed {len(urls)} job search URLs.")
    return urls


def scrape_jobs_from_url(site, url, max_posts=5):
    """
    Scrape job postings from a single URL.
    """
    jobs = []
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        if site == 'indeed':
            cards = soup.find_all('div', class_='jobsearch-SerpJobCard')[:max_posts]
            for card in cards:
                title = card.find('h2', class_='title').get_text(strip=True)
                company = card.find('span', class_='company').get_text(strip=True)
                location = card.find('div', class_='location') or card.find('span', class_='location')
                location = location.get_text(strip=True) if location else ''
                link = 'https://www.indeed.com' + card.find('a')['href']
                jobs.append({'site': site, 'title': title, 'company': company, 'location': location, 'link': link})

        elif site == 'monster':
            cards = soup.find_all('section', class_='card-content')[:max_posts]
            for card in cards:
                title = card.find('h2', class_='title').get_text(strip=True)
                company = card.find('div', class_='company').get_text(strip=True)
                location = card.find('div', class_='location').get_text(strip=True)
                link = card.find('a')['href']
                jobs.append({'site': site, 'title': title, 'company': company, 'location': location, 'link': link})

        elif site == 'simplyhired':
            cards = soup.find_all('div', class_='SerpJob-jobCard')[:max_posts]
            for card in cards:
                title = card.find('a', class_='jobposting-title').get_text(strip=True)
                company = card.find('span', class_='JobPosting-labelWithIcon').get_text(strip=True)
                location = card.find('span', class_='jobposting-location').get_text(strip=True)
                link = 'https://www.simplyhired.com' + card.find('a', class_='jobposting-title')['href']
                jobs.append({'site': site, 'title': title, 'company': company, 'location': location, 'link': link})

        logging.info(f"Scraped {len(jobs)} jobs from {site}.")
    except Exception as e:
        logging.error(f"Failed to scrape {site} at {url}: {e}")
    return jobs


def scrape_jobs(skills):
    """
    Scrape job postings for all skills and sites.
    """
    urls = construct_job_urls(skills)
    all_jobs = []
    for site, url in urls:
        all_jobs.extend(scrape_jobs_from_url(site, url))
    logging.info(f"Total jobs scraped: {len(all_jobs)}")
    return all_jobs

def save_scraped_jobs(jobs, timestamp, scrape_dir="Web-scraped"):
    """
    Save scraped job data into JSON file with timestamp.
    """
    os.makedirs(scrape_dir, exist_ok=True)
    filename = os.path.join(scrape_dir, f"jobs_{timestamp}.json")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=4)
        logging.info(f"Scraped job data saved to: {filename}")
    except Exception as e:
        logging.error(f"Failed to save scraped jobs: {e}")
    return filename

def main():
    parser = argparse.ArgumentParser(description="Job Scraper using saved resume data")
    args = parser.parse_args()

    timestamp = setup_logging()

    data, parsed_ts = load_latest_parsed_data()
    if not data or not data.get('skills'):
        logging.error("No skills found in saved data; please ensure parsing has been run.")
        return

    jobs = scrape_jobs(data['skills'])
    save_scraped_jobs(jobs, timestamp)

    logging.info("Job scraping process completed.")

if __name__ == "__main__":
    main()
