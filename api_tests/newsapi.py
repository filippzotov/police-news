import requests
import csv
from datetime import datetime, timedelta


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


def save_news_to_csv(filename, keyword, articles):
    """
    Appends news articles to a CSV file.

    :param filename: The name of the CSV file
    :param keyword: The keyword associated with the news articles
    :param articles: List of articles to save
    """
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow(
                ["Keyword", "Title", "Description", "URL", "Source", "Published Date"]
            )

        for article in articles:
            writer.writerow(
                [
                    keyword,
                    article.get("title", "N/A"),
                    article.get("description", "N/A"),
                    article.get("url", "N/A"),
                    article.get("source", {}).get("name", "N/A"),
                    article.get("publishedAt", "N/A"),
                ]
            )


if __name__ == "__main__":
    API_KEY = "47f74ca9e0e24b329ef181b966669de6"
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
    from_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    csv_filename = "newsapi_results.csv"

    for keyword in keywords:
        print(f"Fetching news for: {keyword}")
        articles = get_news_from_newsapi(API_KEY, keyword, from_date)

        print(f"Saving news for '{keyword}' to {csv_filename}")
        save_news_to_csv(csv_filename, keyword, articles)

    print(f"News saved to {csv_filename}")
