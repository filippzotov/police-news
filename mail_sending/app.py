import schedule
import time
import csv
import os

from datetime import datetime
from perigon import get_articles_from_perigon
from newsapi import get_articles_from_newsapi
from newsapiai import get_articles_from_newsapiai
from newsdata import get_articles_from_newsdata
from mail_send import send_articles_via_email


from google_sheets import update_google_sheets
from openai_api import chatgpt_answer

# Directory to save results
OUTPUT_DIR = "results"


def extract_titles_from_files(filename):
    """
    Extracts titles and descriptions from a CSV file into a single structure.

    Args:
        filename (str): Path to the CSV file.

    Returns:
        list: A list of dictionaries with 'title' and 'description' keys.
    """
    articles = []
    try:
        with open(filename, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)

            if "Title" not in reader.fieldnames:
                print(f"Skipping {filename}: 'Title' column not found.")
                return articles

            for row in reader:
                if "Title" in row and row["Title"]:
                    title = row["Title"].strip()
                else:
                    continue  # Skip rows without a title

                description = (
                    row["Description"].strip()
                    if "Description" in row
                    and row["Description"]
                    and len(row["Description"].strip()) <= 250
                    else ""
                )

                articles.append({"title": title, "description": description})

    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"An error occurred while processing {filename}: {e}")

    return articles


def get_indexes_to_keep(filename):
    # Extract articles as a list of dictionaries
    articles = extract_titles_from_files(filename)

    # Format the titles and descriptions in a numbered list
    titles_formatted = "\n".join(
        [
            f"{i + 1}. {article['title']}{', description: ' + article['description'] if article['description'] else ''}"
            for i, article in enumerate(articles)
        ]
    )
    print(titles_formatted)
    # Define the prompt
    prompt = """You are NewsEditorGPT, an Artificial Intelligence and a professional news editor. Your role is to efficiently analyze news stories, identify and prioritize related news based on relevance, themes, and current events, and provide organized summaries or selections for publication. This includes ensuring that the content is coherent, accurate, and engaging for the target audience. Your goal is to streamline the news curation process, deliver timely and relevant stories, and continually improve your ability to recognize connections between news items
Your task is to find news based on information from the title, description, and URLs that contain information about police officers (of any position) shooting someone. If there is a mention of a shooting in the news, but it was not committed by a police officer, you should not take this news (after your analysis there may not be any news left, and this is normal). Police shooting news should only be about the state of California (any city in the state of California).
\n
"""
    prompt += f"I have a list of news titles numbered from 1 to {len(articles)}:\n\n"
    prompt += (
        f"{titles_formatted}\n\n"
        "In answer put only Comma-separated indexes of titles to leave."
    )
    print(prompt)
    # Send the prompt to the LLM

    indexes_to_keep = chatgpt_answer(prompt)["response"]
    print(indexes_to_keep)
    # Convert the LLM response into a list of integers (indexes to keep)
    try:
        indexes_to_keep = [
            int(index.strip()) - 1 for index in indexes_to_keep.split(",")
        ]
    except ValueError:
        print("Error processing indexes returned by LLM.")
        return []

    # Filter the titles to keep only the relevant ones

    return indexes_to_keep


def leave_articles_by_index(filename, indexes_to_leave):
    """
    Keeps only the rows at the specified indexes in the given CSV file
    and writes the filtered rows to a new modified file path.

    Args:
        filename (str): Path to the input CSV file.
        indexes_to_leave (list): List of row indexes to keep (0-based indexing).
    """
    try:
        # Generate the new filename by replacing the path
        new_filename = filename.replace(
            "mail_sending/results", "gpt/mail_sending/results_gpt"
        )

        # Ensure the output directory exists
        output_dir = os.path.dirname(new_filename)
        os.makedirs(output_dir, exist_ok=True)

        # Read the entire file
        with open(filename, mode="r", encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            rows = list(reader)  # Read all rows
            headers = rows[0]  # Extract headers
            data_rows = rows[1:]  # Exclude header row

        # Keep only the rows at the specified indexes
        filtered_rows = [headers] + [
            data_rows[i] for i in indexes_to_leave if 0 <= i < len(data_rows)
        ]

        # Write the filtered rows to the new file
        with open(new_filename, mode="w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(filtered_rows)

        print(
            f"New file {new_filename} created successfully. {len(filtered_rows) - 1} rows kept."
        )

    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")


def delete_irrelevant_articles_from_files(filenames):
    for filename in filenames:
        indexes_to_keep = get_indexes_to_keep(filename)
        if indexes_to_keep:
            print(f"Relevant titles from {filename}:\n{indexes_to_keep}")
            leave_articles_by_index(filename, indexes_to_keep)
        else:
            print(f"No relevant titles found in {filename}.")


# Fetch articles from all sources
def fetch_and_send_articles():
    print(f"Job started at {datetime.now()}")
    os.makedirs(
        os.path.dirname("mail_sending/results/newsapi_filtered_results.csv"),
        exist_ok=True,
    )
    os.makedirs(
        os.path.dirname("gpt/mail_sending/results/newsapi_filtered_results.csv"),
        exist_ok=True,
    )

    # Fetch articles from different sources
    get_articles_from_perigon()
    get_articles_from_newsapi()
    get_articles_from_newsapiai()
    get_articles_from_newsdata()

    # # Send articles via email
    print("Articles sent via email.")
    filenames = [
        "mail_sending/results/newsapi_filtered_results.csv",
        "mail_sending/results/newsapiai_filtered_results.csv",
        "mail_sending/results/newsdata_filtered_results.csv",
        "mail_sending/results/goperigon_filtered_results.csv",
    ]
    delete_irrelevant_articles_from_files(filenames)

    update_google_sheets()

    send_articles_via_email()

    print(f"Job completed at {datetime.now()}")


# Schedule the job every 24 hours
schedule.every(24).hours.do(fetch_and_send_articles)

if __name__ == "__main__":
    print("Scheduler started. Fetching and sending articles every 24 hours.")
    fetch_and_send_articles()  # Run immediately on startup
    while True:
        schedule.run_pending()
        time.sleep(1)
