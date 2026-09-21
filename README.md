# Data Procurement Script

This project downloads stock price history and news sentiment data for a set of companies and saves the results as CSV files inside the `data/` folder.

## Requirements

1. Python 3.9+
2. A virtual environment is recommended.
3. Install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `requirements.txt` is not present, install the needed packages manually:

```bash
pip install pandas yfinance requests python-dotenv
```

## Environment setup

Create a `.env` file in the project root with your Alpha Vantage API key:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

This key is required because the script uses Alpha Vantage for news sentiment data.

## How to run

From the project root, run:

```bash
python dataprocurement.py
```

The script will:
- create the `data/prices` and `data/news` folders if needed
- download price data from Yahoo Finance
- download company news data from Alpha Vantage
- save CSV files for each company

## Where to change stock names and metadata

All stock configuration is in the `COMPANIES` dictionary inside `dataprocurement.py`.

```python
COMPANIES = {
    "NVDA": {
        "name": "NVIDIA",
        "yahoo": "NVDA",
        "alpha": "NVDA"
    },
    ...
}
```

To add or modify a stock:

1. Open `dataprocurement.py`
2. Find the `COMPANIES` dictionary
3. Add a new key with the company code, for example `"TSLA"`
4. Set:
   - `name`: the human-readable company name used in CSV output
   - `yahoo`: the stock ticker used by Yahoo Finance
   - `alpha`: the ticker used by Alpha Vantage

Example:

```python
"TSLA": {
    "name": "Tesla",
    "yahoo": "TSLA",
    "alpha": "TSLA"
}
```

## Where to change the news company list

The script only downloads news for selected companies from the `NEWS_COMPANIES` tuple.

```python
NEWS_COMPANIES = ("AAPL", "MSFT", "NFLX", "SAMSUNG")
```

Add or remove company codes here to control which stock news is collected.

## Output files

The script writes these files:

- `data/prices/<COMPANY_CODE>_prices.csv`
- `data/news/<COMPANY_CODE>_news.csv`

If a company is included in `COMPANIES` but not in `NEWS_COMPANIES`, it will still appear in the configuration but will not have news fetched in the main run.

## Notes

- The `START_DATE` and `END_DATE` constants in `dataprocurement.py` control the collection window.
- Samsung has a fallback news fetch path because Alpha Vantage sometimes returns limited or missing results for that ticker.
- The script saves raw output to CSV without additional processing.
