import os
import requests
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from datetime import datetime

# Load local environment variables such as the Alpha Vantage API key.
load_dotenv()

# API key is required for fetching news sentiment data.
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

if not ALPHA_VANTAGE_API_KEY:
    raise ValueError(
        "ALPHA_VANTAGE_API_KEY not found. "
        "Create a .env file and add your API key."
    )

# Date range used for both price and news downloads.
START_DATE = "2016-09-19"
END_DATE = "2026-09-19"

# Main stock configuration.
# Change the list here to add, remove, or rename tracked companies.
# Each entry includes a friendly company name and the ticker codes used for
# Yahoo Finance and Alpha Vantage data sources.
COMPANIES = {
    "NVDA": {
        "name": "NVIDIA",
        "yahoo": "NVDA",
        "alpha": "NVDA"
    },

    "AAPL": {
        "name": "Apple",
        "yahoo": "AAPL",
        "alpha": "AAPL"
    },

    "MSFT": {
        "name": "Microsoft",
        "yahoo": "MSFT",
        "alpha": "MSFT"
    },

    "NFLX": {
        "name": "Netflix",
        "yahoo": "NFLX",
        "alpha": "NFLX"
    },

    "SAMSUNG": {
        "name": "Samsung Electronics",
        "yahoo": "005930.KS",
        "alpha": "005930.KRX"
    }
}

# Only these companies will have news downloaded.
# If you want to include more stocks, add their code here.
NEWS_COMPANIES = ("AAPL", "MSFT", "NFLX", "SAMSUNG")

# Output folders for generated CSV files.
PRICE_DIR = "data/prices"
NEWS_DIR = "data/news"

# Create the output directories if they do not exist yet.
os.makedirs(PRICE_DIR, exist_ok=True)
os.makedirs(NEWS_DIR, exist_ok=True)


# Download historical market prices for one company from Yahoo Finance.
def download_prices(company_code, company_info):

    print("=" * 60)
    print(f"Downloading prices: {company_info['name']}")

    ticker = company_info["yahoo"]

    try:

        data = yf.download(
            ticker,
            start=START_DATE,
            end=END_DATE,
            auto_adjust=False,
            progress=False
        )

        if data.empty:
            print(f"No data returned for {ticker}")
            return

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data.reset_index(inplace=True)

        required_columns = [
            "Date",
            "Open",
            "High",
            "Low",
            "Close",
            "Adj Close",
            "Volume"
        ]

        available_columns = [
            c for c in required_columns if c in data.columns
        ]

        data = data[available_columns]

        data.insert(1, "Ticker", company_code)
        data.insert(2, "Company", company_info["name"])

        filename = f"{PRICE_DIR}/{company_code}_prices.csv"

        data.to_csv(filename, index=False)

        print(f"Saved: {filename}")
        print(f"Rows: {len(data)}")

    except Exception as e:

        print(f"Error downloading {company_info['name']}: {e}")


# Download company news and sentiment data from Alpha Vantage.
# The script stores the article-level data as a CSV in the data/news folder.
def download_news(company_code, company_info):

    print("=" * 60)
    print(f"Downloading news: {company_info['name']}")

    ticker = company_info["alpha"]

    all_news = []

    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "time_from": start.strftime("%Y%m%dT0000"),
        "time_to": end.strftime("%Y%m%dT2359"),
        "limit": 1000,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params=params,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        if "Note" in result or "Information" in result:
            print(result.get("Note") or result["Information"])
            return

        feed = result.get("feed", [])
        print(f"Received {len(feed)} articles")

        for article in feed:
                ticker_relevance = None
                ticker_sentiment_score = None
                ticker_sentiment_label = None

                for ts in article.get(
                    "ticker_sentiment",
                    []
                ):

                    if ts.get("ticker") == ticker:

                        ticker_relevance = ts.get(
                            "relevance_score"
                        )

                        ticker_sentiment_score = ts.get(
                            "ticker_sentiment_score"
                        )

                        ticker_sentiment_label = ts.get(
                            "ticker_sentiment_label"
                        )

                        break

                all_news.append({

                    "Date": article.get(
                        "time_published"
                    ),

                    "Ticker": company_code,

                    "Company": company_info["name"],

                    "Title": article.get(
                        "title"
                    ),

                    "Source": article.get(
                        "source"
                    ),

                    "URL": article.get(
                        "url"
                    ),

                    "Summary": article.get(
                        "summary"
                    ),

                    "Overall_Sentiment_Score":
                        article.get(
                            "overall_sentiment_score"
                        ),

                    "Overall_Sentiment_Label":
                        article.get(
                            "overall_sentiment_label"
                        ),

                    "Ticker_Relevance":
                        ticker_relevance,

                    "Ticker_Sentiment_Score":
                        ticker_sentiment_score,

                    "Ticker_Sentiment_Label":
                        ticker_sentiment_label
                })

    except Exception as e:
        print(f"Error downloading news: {e}")

    if not all_news and company_code == "SAMSUNG":

        try:
            for article in yf.Ticker(company_info["yahoo"]).news:
                content = article.get("content", {})
                provider = content.get("provider", {})
                canonical_url = content.get("canonicalUrl", {})

                all_news.append({
                    "Date": content.get("pubDate"),
                    "Ticker": company_code,
                    "Company": company_info["name"],
                    "Title": content.get("title"),
                    "Source": provider.get("displayName"),
                    "URL": canonical_url.get("url") or content.get("previewUrl"),
                    "Summary": content.get("summary") or content.get("description"),
                    "Overall_Sentiment_Score": None,
                    "Overall_Sentiment_Label": None,
                    "Ticker_Relevance": None,
                    "Ticker_Sentiment_Score": None,
                    "Ticker_Sentiment_Label": None
                })

            print(f"Samsung fallback received {len(all_news)} articles")

        except Exception as e:
            print(f"Error downloading Samsung fallback news: {e}")

    if not all_news:

        print("No news found.")

        return

    news_df = pd.DataFrame(all_news)

    news_df.drop_duplicates(
        subset=["URL"],
        inplace=True
    )

    news_df.sort_values(
        "Date",
        inplace=True
    )

    filename = f"{NEWS_DIR}/{company_code}_news.csv"

    news_df.to_csv(
        filename,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Saved: {filename}")
    print(f"Articles: {len(news_df)}")


def main():

    # This is the main orchestration step for the project.
    # It collects news for the configured company list and prints a simple status.
    print("\n")
    print("=" * 70)
    print("10-YEAR STOCK + NEWS DATA COLLECTION")
    print("=" * 70)

    print(f"Period: {START_DATE} → {END_DATE}")

    for company_code in NEWS_COMPANIES:

        company_info = COMPANIES[company_code]

        download_news(
            company_code,
            company_info
        )

    print("\n")
    print("=" * 70)
    print("DATA COLLECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
