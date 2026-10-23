
import os
import logging
import requests
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pandas as pd

logger = logging.getLogger(__name__)

# CSV extraction function
def extract_csv(path: str | Path, **read_kwargs) -> pd.DataFrame:
    """Read/Extract a CSV file into a pandas DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    df = pd.read_csv(path, **read_kwargs)
    logger.info("Extracted %d rows, %d columns from %s", *df.shape, path.name)
    return df

# JSON extraction function
def extract_api(url: str, params:dict | None = None, timeout: int = 10):
    """Fetch JSON from a REST API with basic error handling."""
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        logger.error("API request failed for %s: %s", url, exc)
        raise

# MySQL extraction function
load_dotenv()

def get_engine():
    url = URL.create(
        "mysql+pymysql",
        username = os.environ["DB_USER"],
        password = os.environ["DB_PASSWORD"],
        host = os.environ["DB_HOST"],
        port = int(os.environ.get["DB_PORT", 3306]),
        database = os.environ["DB_NAME"],
    )
    return create_engine(url)

def extract_mysql(query: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SQL query and return the result as a pandas DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)


def save_raw(df: pd.DataFrame, name: str, raw_dir :str = "data/raw") -> Path:
    """ Save an untouched extract, never overwriteing an earlier one."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / f"{name}.csv"
    if file_path.exists():
        raise FileExistsError(f"File already exists: {file_path}")
    df.to_csv(file_path, index=False)
    logger.info("Saved raw extract to %s", file_path)
    return file_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    data = extract_api("https://date.nager.at/api/v3/PublicHolidays/2024/US")
    holidays = pd.json_normalize(data)
    save_raw(holidays, "us_public_holidays_2024")