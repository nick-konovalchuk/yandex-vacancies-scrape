# yandex-vacancies-scrape
The `main.py` script is designed to track the diff of Yandex vacancies.  
The first run creates: 
- `seen.csv` with all* currently active Yandex vacancies 
- `add.csv` with same data as `seen.csv`
- `delete.csv`, empty for now  

Subsequent runs rewrite all 3 files:
- `seen.csv` with, again, all* currently active Yandex vacancies 
- `add.csv` with vacancies that weren't in previous `seen.csv`
- `delete.csv` with vacancies that were in previous `seen.csv`, but not in new one

\* The url with search filters is hard-coded. You can change in by changing the `_URL` variable

## Usage
If you don't use Python regularly, here are the steps for you:
1. Have Python 3 installed
2. Clone the repo and cd into it
3. Create and activate a virtual environment (optional, but strongly advised)
    ```shell
    python -m venv venv
    . venv/bin/activate  # Linux 
    ```
4. Install dependencies 
    ```shell
    pip install -r requirements.txt
    ```
5. Run the script
   ```shell
   python main.py
   ```
## Contribution
If you want some features/changes (like config files instead of manually changing the source code), 
please open an issue
## Q&A
- Why did you decide to use CSV files?  
    So I can easily copy and paste to a shared Google Sheet
