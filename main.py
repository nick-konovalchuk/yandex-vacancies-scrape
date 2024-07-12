import csv
import logging
import os
import random
import time
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from bs4 import BeautifulSoup
from bs4 import ResultSet
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from tqdm.auto import tqdm


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.yandex.ru",
    "Connection": "keep-alive",
}
_URL = (
    "https://yandex.ru/jobs/vacancies?"
    "work_modes=mixed&work_modes=remote&professions=ml-developer"
)

_BASE_DATA_DIR = "data"
_SEEN_PATH = os.path.join(_BASE_DATA_DIR, "seen.csv")
_ADD_PATH = os.path.join(_BASE_DATA_DIR, "delete.csv")
_DELETE_PATH = os.path.join(_BASE_DATA_DIR, "add.csv")


def get_random_timeout(min_: float = 1.5, mean: float = 4) -> float:
    return max(min_, random.gauss(mean, 1))


def get_whole_page_content(url: str) -> str:
    options = Options()
    options.add_argument("--headless")
    with webdriver.Firefox(options=options) as driver:
        driver.get(url)
        last_height = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(get_random_timeout())
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        return driver.page_source


def scrape_vacancy(url: str, sess: requests.Session) -> Tuple[str, str]:
    service_name = None
    position_name = None
    try:
        content = sess.get(url, headers=_HEADERS).content
        soup = BeautifulSoup(content, "html.parser")
        position_name = soup.find("h1").get_text()
        service_name = soup.find(class_="lc-jobs-tags-block__service-name").get_text()
    except (requests.RequestException, AttributeError):
        logging.warning("Failed to scrape a vacancy")
    return position_name, service_name


def scrape_vacancies(
    vacancies: ResultSet, urls_ro_delete: Set[str]
) -> Tuple[List[Optional[str]], List[Optional[str]]]:
    position_names = []
    service_names = []
    with requests.Session() as sess:
        for vacancy in tqdm(vacancies, desc="Scraping..."):
            url = "https://yandex.ru" + vacancy.attrs["href"]
            if url in urls_ro_delete:
                urls_ro_delete.remove(url)
                continue
            position_name, service_name = scrape_vacancy(url, sess)
            position_names.append(position_name)
            service_names.append(service_name)
            time.sleep(get_random_timeout())
    return position_names, service_names


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
    logging.info("Scrolling vacancies page...")
    content = get_whole_page_content(_URL)

    soup = BeautifulSoup(content, "html.parser")
    vacancies = soup.find_all(class_="lc-jobs-vacancy-card__link")
    logging.info(f"Found {len(vacancies)} vacancies!")

    os.makedirs(_BASE_DATA_DIR, exist_ok=True)
    if not os.path.exists(_SEEN_PATH):
        seen_rows = []
    else:
        with open(_SEEN_PATH) as f:
            seen_rows = list(csv.reader(f))[1:]  # skipping header
    urls_to_delete = {i[1] for i in seen_rows}
    position_names, service_names = scrape_vacancies(vacancies, urls_to_delete)
    csv_header = ["stage", "link", "position", "service", "rating", "comments"]
    rows_to_keep = [csv_header]
    rows_to_delete = [csv_header]
    for row in seen_rows:
        if row[1] in urls_to_delete:
            rows_to_delete.append(row)
        else:
            rows_to_keep.append(row)

    rows_to_add = [csv_header]
    for position_name, service_name in zip(position_names, service_names):
        rows_to_keep.append([position_name, service_name])
        rows_to_add.append([position_name, service_name])

    logging.info(f"Saving {len(rows_to_keep)-1} active vacancies...")
    with open(_SEEN_PATH, mode="w", newline="") as f:
        csv.writer(f).writerows(rows_to_keep)

    logging.info(f"Saving {len(rows_to_delete)-1} vacancies to be deleted...")
    with open(_DELETE_PATH, mode="w", newline="") as f:
        csv.writer(f).writerows(rows_to_delete)

    logging.info(f"Saving {len(rows_to_add)-1} vacancies to be added...")
    with open(_ADD_PATH, mode="w", newline="") as f:
        csv.writer(f).writerows(rows_to_add)
