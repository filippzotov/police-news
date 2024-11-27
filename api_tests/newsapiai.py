import requests
import csv
from datetime import datetime
from fuzzywuzzy import fuzz


def is_similar_title(existing_title, new_title, threshold=90):
    """
    Check if two titles are similar using a similarity threshold.

    :param existing_title: The title already in the CSV file
    :param new_title: The title of the new article
    :param threshold: The similarity threshold (default is 90)
    :return: True if the titles are similar, False otherwise
    """
    return fuzz.ratio(existing_title.lower(), new_title.lower()) >= threshold


def read_existing_titles(filename):
    """
    Reads existing article titles from the CSV file.

    :param filename: The name of the CSV file
    :return: A set of titles from the file
    """
    existing_titles = []
    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                existing_titles.append(row["Title"])
    except FileNotFoundError:
        # File does not exist yet, so no existing titles
        pass
    return existing_titles


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


def save_articles_to_csv(filename, keyword, articles):
    """
    Appends articles to a CSV file after checking for duplicates.

    :param filename: The name of the CSV file
    :param keyword: The keyword associated with the articles
    :param articles: List of articles to save
    """
    existing_titles = read_existing_titles(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write the header if the file is empty
        if file.tell() == 0:
            writer.writerow(
                [
                    "Keyword",
                    "URI",
                    "Title",
                    "Body",
                    "URL",
                    "Source",
                    "Language",
                    "Date",
                    "Time",
                    "Concepts",
                ]
            )

        for article in articles:
            new_title = article.get("title", "N/A")

            # Check if the article title is similar to any existing title
            if any(
                is_similar_title(existing_title, new_title)
                for existing_title in existing_titles
            ):
                print(f"Skipping duplicate or similar article: {new_title}")
                continue

            concepts = ", ".join(
                [concept["label"]["eng"] for concept in article.get("concepts", [])]
            )
            writer.writerow(
                [
                    keyword,
                    article.get("uri", "N/A"),
                    new_title,
                    article.get("body", "N/A"),
                    article.get("url", "N/A"),
                    article.get("source", {}).get("title", "N/A"),
                    article.get("lang", "N/A"),
                    article.get("date", "N/A"),
                    article.get("time", "N/A"),
                    concepts,
                ]
            )
            # Add the title to existing_titles to prevent rechecking in the same run
            existing_titles.append(new_title)


if __name__ == "__main__":
    API_KEY = "b7e606c3-800f-4d4c-aa5c-57f38fd4d530"  # Replace with your API key
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
    csv_filename = "newsapiai_articles.csv"

    for keyword in keywords:
        print(f"Fetching articles for keyword: {keyword}")
        articles = get_articles_from_event_registry(
            API_KEY, keyword, source_location_uri, ignore_source_group_uri
        )

        if articles:
            print(
                f"Saving {len(articles)} articles for keyword '{keyword}' to {csv_filename}"
            )
            save_articles_to_csv(csv_filename, keyword, articles)
        else:
            print(f"No articles found for keyword '{keyword}'.")

    print(f"All articles saved to {csv_filename}")
