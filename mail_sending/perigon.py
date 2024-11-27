import requests
import csv
from datetime import datetime
import time

from fuzzywuzzy import fuzz


def remove_duplicate_articles(articles):
    """
    Removes duplicate articles based on URL and optionally checks for similar articles.

    :param articles: List of articles to process
    :return: List of unique articles
    """
    unique_articles = []
    seen_urls = set()

    for article in articles:
        url = article.get("URL", "N/A")
        if url != "N/A" and url in seen_urls:
            continue

        # Add URL to the set and include the article
        seen_urls.add(url)
        unique_articles.append(article)

    return unique_articles


def remove_similar_articles(articles, similarity_threshold=90):
    """
    Removes articles with similar titles or descriptions based on a similarity threshold.

    :param articles: List of articles to process
    :param similarity_threshold: Minimum similarity percentage to consider articles as duplicates
    :return: List of unique articles
    """
    unique_articles = []
    titles_descriptions = []

    for article in articles:
        title = article.get("Title", "").lower()
        description = article.get("Description", "").lower()

        if any(
            fuzz.ratio(title, existing[0]) > similarity_threshold
            or fuzz.ratio(description, existing[1]) > similarity_threshold
            for existing in titles_descriptions
        ):
            continue

        # Add the title and description pair to the list and include the article
        titles_descriptions.append((title, description))
        unique_articles.append(article)

    return unique_articles


def get_news_from_goperigon(api_key, query, show_reprints=False):
    """
    Fetches news articles for a given query from the GoPerigon API.

    :param api_key: Your API key for GoPerigon API
    :param query: The query string to search for
    :param show_reprints: Whether to include reprints in the results
    :return: List of articles
    """

    base_url = "https://api.goperigon.com/v1/all"
    today_date = datetime.now().strftime("%Y-%m-%d")
    params = {
        "apiKey": api_key,
        "q": query,
        "showReprints": str(show_reprints).lower(),
        "from": today_date,
        "to": today_date,
        "state": "CA",  # Add states as a comma-separated string
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("articles", [])
    else:
        print(
            f"Failed to fetch news for query: {query}. Status code: {response.status_code}"
        )
        return []


def read_news_from_csv(filename):
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


def save_news_to_csv(filename, articles):
    """
    Appends news articles to a CSV file.

    :param filename: The name of the CSV file
    :param articles: List of articles to save
    """
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow(
                [
                    "Query",
                    "Published Date",
                    "Title",
                    "Description",
                    "URL",
                    "Authors",
                    "Source",
                    "Country",
                    "Language",
                    "Image URL",
                ]
            )

        for article in articles:
            writer.writerow(
                [
                    article.get("query", "N/A"),
                    article.get("pubDate", "N/A"),
                    article.get("title", "N/A"),
                    article.get("description", "N/A"),
                    article.get("url", "N/A"),
                    article.get("authorsByline", "N/A"),
                    article.get("source", {}).get("domain", "N/A"),
                    article.get("country", "N/A"),
                    article.get("language", "N/A"),
                    article.get("imageUrl", "N/A"),
                ]
            )


import os
from dotenv import load_dotenv
from decouple import config


def get_articles_from_perigon():
    PERIGON_KEY = config("PERIGON_KEY")
    queries = [
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
    raw_csv_filename = "mail_sending/results/goperigon_results1.csv"
    filtered_csv_filename = "mail_sending/results/goperigon_filtered_results.csv"

    all_articles = []

    # Fetch and save raw articles
    for query in queries:
        print(f"Fetching news for query: {query}")
        articles = get_news_from_goperigon(PERIGON_KEY, query)

        # Add the query to each article for context
        for article in articles:
            article["query"] = query

        all_articles.extend(articles)

        print(f"Found {len(articles)} articles for query: {query}")

        # Introduce a delay before the next request
        time.sleep(2)  # Delay for 2 seconds

    print(f"Saving raw articles to {raw_csv_filename}")
    save_news_to_csv(raw_csv_filename, all_articles)
    print(f"Raw articles saved to {raw_csv_filename}")

    # Read back raw articles for processing
    print(f"Reading raw articles from {raw_csv_filename}")
    all_articles = read_news_from_csv(raw_csv_filename)
    print(f"Loaded {len(all_articles)} raw articles from file")

    # Remove duplicate articles based on URL
    print("Removing duplicate articles by URL...")
    all_articles = remove_duplicate_articles(all_articles)
    print(f"Remaining articles after URL deduplication: {len(all_articles)}")

    # Optionally remove similar articles based on title
    print("Removing similar articles by title...")
    all_articles = remove_similar_articles(all_articles, similarity_threshold=50)
    print(f"Remaining articles after title deduplication: {len(all_articles)}")

    # Save filtered articles to a new file
    print(f"Saving filtered articles to {filtered_csv_filename}")
    save_filtered_news_to_csv(filtered_csv_filename, all_articles)
    print(f"Filtered articles saved to {filtered_csv_filename}")


if __name__ == "__main__":
    get_articles_from_perigon()
