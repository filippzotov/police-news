import requests
import csv
from datetime import datetime


def get_news_from_goperigon(api_key, query, show_reprints=False):
    """
    Fetches news articles for a given query from the GoPerigon API.

    :param api_key: Your API key for GoPerigon API
    :param query: The query string to search for
    :param show_reprints: Whether to include reprints in the results
    :return: List of articles
    """
    states = [
        "California",
    ]

    base_url = "https://api.goperigon.com/v1/all"
    today_date = datetime.now().strftime("%Y-%m-%d")
    params = {
        "apiKey": api_key,
        "q": query,
        "showReprints": str(show_reprints).lower(),
        "from": today_date,
        "to": today_date,
        "state": "CA, TN, WA, IL",  # Add states as a comma-separated string
    }

    response = requests.get(base_url, params=params)
    print(response.json())
    if response.status_code == 200:
        data = response.json()
        return data.get("articles", [])
    else:
        print(
            f"Failed to fetch news for query: {query}. Status code: {response.status_code}"
        )
        return []


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
                    "Title",
                    "Description",
                    "URL",
                    "Authors",
                    "Source",
                    "Published Date",
                    "Country",
                    "Language",
                    "Image URL",
                ]
            )

        for article in articles:
            writer.writerow(
                [
                    article.get("query", "N/A"),
                    article.get("title", "N/A"),
                    article.get("description", "N/A"),
                    article.get("url", "N/A"),
                    article.get("authorsByline", "N/A"),
                    article.get("source", {}).get("domain", "N/A"),
                    article.get("pubDate", "N/A"),
                    article.get("country", "N/A"),
                    article.get("language", "N/A"),
                    article.get("imageUrl", "N/A"),
                ]
            )


if __name__ == "__main__":
    API_KEY = "1527025f-f536-4433-ab4c-77150b5187d1"  # Replace with your API key
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
    csv_filename = "goperigon_results.csv"

    all_articles = []

    for query in queries:
        print(f"Fetching news for query: {query}")
        articles = get_news_from_goperigon(API_KEY, query)

        # Add the query to each article for context
        for article in articles:
            article["query"] = query

        all_articles.extend(articles)

        print(f"Found {len(articles)} articles for query: {query}")

    print(f"Saving all articles to {csv_filename}")
    save_news_to_csv(csv_filename, all_articles)

    print(f"News saved to {csv_filename}")
