import requests
import csv
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import time


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


def is_similar(
    existing_title, existing_description, new_title, new_description, threshold=90
):
    """
    Check if two articles are similar based on title and description using a similarity threshold.

    :param existing_title: The title already in the list
    :param existing_description: The description already in the list
    :param new_title: The title of the new article
    :param new_description: The description of the new article
    :param threshold: The similarity threshold (default is 90)
    :return: True if the articles are similar, False otherwise
    """
    title_similarity = fuzz.ratio(existing_title.lower(), new_title.lower())
    description_similarity = fuzz.ratio(
        existing_description.lower(), new_description.lower()
    )
    return title_similarity >= threshold or description_similarity >= threshold


def get_articles_from_event_registry(
    api_key, keyword, source_location_uri, ignore_source_group_uri, articles_count=100
):
    """
    Fetches articles from the Event Registry API for a given keyword.

    :param api_key: Your API key for Event Registry API
    :param keyword: The keyword to search for
    :param source_location_uri: The location URI to filter articles
    :param ignore_source_group_uri: URI to ignore specific source groups
    :param articles_count: Number of articles to fetch
    :return: List of articles
    """
    url = "https://eventregistry.org/api/v1/article/getArticles"
    payload = {
        "action": "getArticles",
        "keyword": keyword,
        "sourceLocationUri": source_location_uri,
        "ignoreSourceGroupUri": ignore_source_group_uri,
        "articlesPage": 1,
        "articlesCount": articles_count,
        "articlesSortBy": "date",
        "articlesSortByAsc": False,
        "dataType": ["news", "pr"],
        "forceMaxDataTimeWindow": 31,
        "resultType": "articles",
        "apiKey": api_key,
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data.get("articles", {}).get("results", [])
    else:
        print(f"Failed to fetch articles. Status code: {response.status_code}")
        return []


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
            "Published Date", "1970-01-01"
        )  # Default to an old date if missing
        try:
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
            if pub_date >= cutoff_date:
                recent_articles.append(article)
            else:
                print(
                    f"Skipping old article published on {pub_date_str}: {article.get('title', 'N/A')}"
                )
        except ValueError:
            print(f"Invalid date format for article: {article.get('title', 'N/A')}")
            continue

    return recent_articles


def deduplicate_articles(articles, threshold=90):
    """
    Removes duplicate or similar articles based on title and description.

    :param articles: List of articles
    :param threshold: Similarity threshold for deduplication
    :return: List of unique articles
    """
    unique_articles = []
    seen_data = []

    for article in articles:
        new_title = article.get("Title", "N/A")
        new_description = article.get("Description", "N/A")

        if any(
            is_similar(
                existing_title,
                existing_description,
                new_title,
                new_description,
                threshold,
            )
            for existing_title, existing_description in seen_data
        ):
            print(f"Skipping duplicate or similar article: {new_title}")
            continue

        unique_articles.append(article)
        seen_data.append((new_title, new_description))

    return unique_articles


def save_news_to_csv(filename, articles):
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
                "URI",
                "Title",
                "Description",
                "URL",
                "Source",
                "Language",
                "Time",
                "Concepts",
            ]
        )

        for article in articles:
            concepts = ", ".join(
                [concept["label"]["eng"] for concept in article.get("concepts", [])]
            )
            writer.writerow(
                [
                    article.get("keyword", "N/A"),
                    article.get("date", "N/A"),
                    article.get("uri", "N/A"),
                    article.get("title", "N/A"),
                    article.get("body", "N/A"),
                    article.get("url", "N/A"),
                    article.get("source", {}).get("title", "N/A"),
                    article.get("lang", "N/A"),
                    article.get("time", "N/A"),
                    concepts,
                ]
            )


import os
from dotenv import load_dotenv
from decouple import config


def get_articles_from_newsapiai():
    NEWSAPIAI_KEY = config("NEWSAPIAI_KEY")  # Fetch the API key from .env
    if not NEWSAPIAI_KEY:
        raise ValueError("NEWSAPIAI_KEY not found in .env file")
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
    ]  # Array of keywords
    source_location_uri = [
        "http://en.wikipedia.org/wiki/California",
        "http://en.wikipedia.org/wiki/Los_Angeles",
        "http://en.wikipedia.org/wiki/Orange_County,_California",
        "http://en.wikipedia.org/wiki/Riverside_County,_California",
        "http://en.wikipedia.org/wiki/San_Bernardino_County,_California",
    ]
    ignore_source_group_uri = "paywall/paywalled_sources"
    raw_csv_filename = "mail_sending/results/newsapiai_results.csv"
    filtered_csv_filename = "mail_sending/results/newsapiai_filtered_results.csv"

    all_articles = []

    for keyword in keywords:
        print(f"Fetching articles for keyword: {keyword}")
        articles = get_articles_from_event_registry(
            NEWSAPIAI_KEY, keyword, source_location_uri, ignore_source_group_uri
        )

        # Tag each article with the keyword for context
        for article in articles:
            article["keyword"] = keyword

        all_articles.extend(articles)

        time.sleep(2)

    print(f"Saving {len(all_articles)} raw articles to {raw_csv_filename}")
    save_news_to_csv(raw_csv_filename, all_articles)
    print(f"Raw articles saved to {raw_csv_filename}")

    # Read raw articles for processing
    print(f"Reading raw articles from {raw_csv_filename}")
    all_articles = read_news_from_csv(raw_csv_filename)
    print(f"Loaded {len(all_articles)} raw articles from file")

    # Filter articles older than 7 days
    print("Filtering articles older than 7 days...")
    recent_articles = filter_recent_articles(all_articles, days=7)

    # Remove duplicates and similar articles across all recent data
    print("Removing duplicates and similar articles across all recent data...")
    unique_articles = deduplicate_articles(recent_articles, threshold=70)

    # Save filtered articles to a new file
    print(f"Saving {len(unique_articles)} unique articles to {filtered_csv_filename}")
    save_filtered_news_to_csv(filtered_csv_filename, unique_articles)
    print(f"Filtered articles saved to {filtered_csv_filename}")


if __name__ == "__main__":
    get_articles_from_newsapiai()
