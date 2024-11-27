import requests
import csv
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import time


def read_articles_from_csv(filename):
    import csv

    articles = []
    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            articles.append(row)
    return articles


def save_filtered_news_to_csv(filename, articles):
    import csv

    keys = articles[0].keys() if articles else []
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(articles)


def get_news_for_keyword(api_key, keyword, regions, country="us"):
    """
    Fetches news articles for a single keyword from the newsdata.io API.

    :param api_key: Your API key for newsdata.io
    :param keyword: The keyword to search for
    :param country: Country code for filtering news (default is 'us')
    :return: List of articles for the given keyword
    """
    base_url = "https://newsdata.io/api/1/latest"
    params = {
        "apikey": api_key,
        "q": keyword,
        "country": country,
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])
    else:
        print(
            f"Failed to fetch news for keyword: {keyword}. Status code: {response.status_code}"
        )
        return []


def is_similar(existing_title, new_title, threshold=90):
    """
    Check if two articles are similar based on title using a similarity threshold.

    :param existing_title: The title already in the list
    :param new_title: The title of the new article
    :param threshold: The similarity threshold (default is 90)
    :return: True if the articles are similar, False otherwise
    """
    return fuzz.ratio(existing_title.lower(), new_title.lower()) >= threshold


def is_relevant(article, keyword, threshold=60):
    """
    Check if an article is relevant to the given keyword using a similarity threshold.

    :param article: The article to check
    :param keyword: The keyword to compare against
    :param threshold: The similarity threshold (default is 60)
    :return: True if the article is relevant, False otherwise
    """
    title = article.get("title", "").lower()
    description = article.get("description", "") or ""  # Handle None descriptions
    keyword = keyword.lower()

    # Check relevance using both title and description
    title_similarity = fuzz.partial_ratio(keyword, title)
    description_similarity = fuzz.partial_ratio(keyword, description)

    return title_similarity >= threshold or description_similarity >= threshold


def filter_recent_articles(articles, days=7):
    """
    Filters articles to include only those published within the last `days` days.

    :param articles: List of articles
    :param days: Number of days to consider as recent (default is 7)
    :return: List of recent articles
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_articles = []

    for article in articles:
        pub_date_str = article.get(
            "Published Date", ""
        )  # Use an empty string if pubDate is missing
        if not pub_date_str:
            print(
                f"Missing publication date for article: {article.get('title', 'N/A')}"
            )
            continue

        try:
            # Parse the date in YYYY-MM-DD HH:MM:SS format
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")

            # Filter articles based on the cutoff date
            if pub_date >= cutoff_date:
                recent_articles.append(article)
            else:
                print(
                    f"Skipping old article published on {pub_date_str}: {article.get('title', 'N/A')}"
                )
        except ValueError:
            print(
                f"Invalid date format for article: {article.get('title', 'N/A')} ({pub_date_str})"
            )
            continue

    return recent_articles


def deduplicate_articles(articles, threshold=90):
    """
    Removes duplicate or similar articles based on title.

    :param articles: List of articles
    :param threshold: Similarity threshold for deduplication
    :return: List of unique articles
    """
    unique_articles = []
    seen_titles = []

    for article in articles:
        new_title = article.get("Title", "N/A")

        if any(
            is_similar(existing_title, new_title, threshold)
            for existing_title in seen_titles
        ):
            print(f"Skipping duplicate or similar article: {new_title}")
            continue

        unique_articles.append(article)
        seen_titles.append(new_title)

    return unique_articles


def save_articles_to_csv(filename, articles):
    """
    Saves unique articles to a CSV file.

    :param filename: The name of the CSV file
    :param articles: List of articles to save
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write the header
        writer.writerow(
            [
                "Keyword",
                "Published Date",
                "Title",
                "URL",
                "Source",
            ]
        )

        for article in articles:
            writer.writerow(
                [
                    article.get("keyword", "N/A"),
                    article.get("pubDate", "N/A"),
                    article.get("title", "N/A"),
                    article.get("link", "N/A"),
                    article.get("source_id", "N/A"),
                ]
            )


import os
from dotenv import load_dotenv
from decouple import config


def get_articles_from_newsdata():
    NEWSDATA_KEY = config("NEWSDATA_KEY")  # Fetch the API key from .env
    if not NEWSDATA_KEY:
        raise ValueError("NEWSDATA_KEY not found in .env file")

    keywords = [
        "officer involved shooting",
        "unarmed person shot by the police",
        "police shooting",
        "deputy shooting",
        "officer involved shooting",
        "deputy involved shooting",
        "shots fired by police",
        "police killing",
        "suspect shot at",
        "man killed by police",
        "woman killed by police",
        "CHP shooting",
        "park ranger shooting",
        "law enforcement shooting",
        "police use of deadly force",
        "person died in custody",
        "death in custody of police",
    ]
    regions = [
        "los angeles county-california-united states of america",
        "orange county-california-united states of america",
        "riverside county-california-united states of america",
        "san bernardino county-california-united states of america",
    ]
    country = "us"
    raw_csv_filename = "mail_sending/results/newsdata_results.csv"
    filtered_csv_filename = "mail_sending/results/newsdata_filtered_results.csv"
    all_articles = []

    for keyword in keywords:
        print(f"Fetching news for: {keyword}")
        articles = get_news_for_keyword(NEWSDATA_KEY, keyword, regions, country)

        # Filter articles by relevance to the keyword
        relevant_articles = [
            article for article in articles if is_relevant(article, keyword)
        ]

        # Tag each article with the keyword for context
        for article in relevant_articles:
            article["keyword"] = keyword

        all_articles.extend(relevant_articles)
        time.sleep(2)  # Add a delay to avoid rate limiting

    # Save raw articles before filtering
    print(f"Saving {len(all_articles)} raw articles to {raw_csv_filename}")
    save_articles_to_csv(raw_csv_filename, all_articles)
    print(f"Raw articles saved to {raw_csv_filename}")

    # Read raw articles from file for processing
    print(f"Reading raw articles from {raw_csv_filename}")
    all_articles = read_articles_from_csv(raw_csv_filename)
    print(f"Loaded {len(all_articles)} raw articles from file")

    # Filter articles older than 7 days
    print("Filtering articles older than 7 days...")
    recent_articles = filter_recent_articles(all_articles, days=7)

    # Remove duplicates and similar articles across all recent data
    print("Removing duplicates and similar articles across all recent data...")
    unique_articles = deduplicate_articles(recent_articles, threshold=90)

    # Save filtered articles to a new file
    print(f"Saving {len(unique_articles)} unique articles to {filtered_csv_filename}")
    save_filtered_news_to_csv(filtered_csv_filename, unique_articles)
    print(f"Filtered articles saved to {filtered_csv_filename}")


if __name__ == "__main__":
    get_articles_from_newsdata()
