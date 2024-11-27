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


def get_news_from_newsapi(api_key, keyword, from_date, sort_by="popularity"):
    """
    Fetches news articles for a single keyword from the NewsAPI.

    :param api_key: Your API key for NewsAPI
    :param keyword: The keyword to search for
    :param from_date: The starting date for the news search (YYYY-MM-DD format)
    :param sort_by: Criteria to sort the news articles (default is 'popularity')
    :return: List of articles for the given keyword
    """
    url = "https://newsapi.org/v2/everything"
    params = {"q": keyword, "from": from_date, "sortBy": sort_by, "apiKey": api_key}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            print(f"API returned error: {data.get('message')}")
            return []
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
    title = article.get(
        "title", ""
    ).lower()  # Default to an empty string if title is missing
    description = (
        article.get("description", "") or ""
    )  # Handle None by defaulting to an empty string
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
        )  # Use an empty string if publishedAt is missing
        if not pub_date_str:
            print(
                f"Missing publication date for article: {article.get('title', 'N/A')}"
            )
            continue

        try:
            # Parse the date in ISO 8601 format (e.g., 2024-11-18T22:00:01Z)
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ")

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
            ["Keyword", "Published Date", "Title", "Description", "URL", "Source"]
        )

        for article in articles:
            writer.writerow(
                [
                    article.get("keyword", "N/A"),
                    article.get("publishedAt", "N/A"),
                    article.get("title", "N/A"),
                    article.get("description", "N/A"),
                    article.get("url", "N/A"),
                    article.get("source", {}).get("name", "N/A"),
                ]
            )


from decouple import config


def get_articles_from_newsapi():
    NEWSAPI_KEY = config("NEWSAPI_KEY")  # Fetch the API key from .env
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY not found in .env file")
    keywords = [
        "officer involved shooting california",
        "unarmed person shot by the police california",
        "police shooting california",
        "deputy shooting california",
        "officer involved shooting california",
        "deputy involved shooting california",
        "shots fired by police california",
        "police killing california",
        "suspect shot at california",
        "man killed by police california",
        "woman killed by police california",
        "CHP shooting california",
        "park ranger shooting california",
        "law enforcement shooting california",
        "police use of deadly force california",
        "person died in custody california",
        "death in custody of police california",
    ]
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    raw_csv_filename = "mail_sending/results/newsapi_results.csv"
    filtered_csv_filename = "mail_sending/results/newsapi_filtered_results.csv"

    all_articles = []

    # Fetch and save raw articles
    for keyword in keywords:
        print(f"Fetching news for: {keyword}")
        articles = get_news_from_newsapi(NEWSAPI_KEY, keyword, from_date)

        # Filter articles by relevance to the keyword
        relevant_articles = [
            article for article in articles if is_relevant(article, keyword)
        ]

        # Tag each article with the keyword for context
        for article in relevant_articles:
            article["keyword"] = keyword

        all_articles.extend(relevant_articles)

        time.sleep(2)  # Add a delay to avoid hitting rate limits

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
    unique_articles = deduplicate_articles(recent_articles, threshold=90)

    # Save filtered articles to a new file
    print(f"Saving {len(unique_articles)} unique articles to {filtered_csv_filename}")
    save_filtered_news_to_csv(filtered_csv_filename, unique_articles)
    print(f"Filtered articles saved to {filtered_csv_filename}")


if __name__ == "__main__":
    get_articles_from_newsapi()
