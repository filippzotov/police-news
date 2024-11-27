import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import os

# Path to your service account JSON file
SERVICE_ACCOUNT_FILE = "mail_sending/chrome-backbone-442409-b7-6ad37d9ca6e1.json"

# Scopes for the APIs
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Authenticate and initialize the client
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)


def update_google_sheet(sheet_id, csv_file_path, worksheet_name):
    """
    Update an existing Google Sheet by adding or updating a worksheet with data from a CSV file.

    Args:
        sheet_id (str): The ID of the Google Sheet.
        csv_file_path (str): Path to the CSV file.
        worksheet_name (str): Name of the worksheet to update or create.
    """
    # Load CSV data into a DataFrame
    if not os.path.exists(csv_file_path):
        return
    df = pd.read_csv(csv_file_path)

    # Replace NaN, inf, and -inf with default values (e.g., 0 or empty string)
    df = df.replace([float("inf"), float("-inf")], 0)  # Replace infinity values
    df = df.fillna("")  # Replace NaN with empty strings

    # Open the Google Sheet by ID
    sheet = gc.open_by_key(sheet_id)

    # Check if the worksheet exists
    try:
        worksheet = sheet.worksheet(worksheet_name)
        # If it exists, clear its content
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        # If it doesn't exist, create a new worksheet
        worksheet = sheet.add_worksheet(title=worksheet_name, rows=100, cols=20)

    # Update the worksheet with sanitized data
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print(f"Updated worksheet '{worksheet_name}' in sheet: {sheet_id}")


def update_google_sheets():
    # Example usage
    # Existing Google Sheet ID
    sheet_id = "1c5o3QM_n-3DeenZKAZa0HeTBGcKQ2XYtBrYT3w7JVsM"
    sheet_id2 = "1pBvCrQqw01KfEw9h9-LAyvYC5p7NJ-dsWQK_0XhQGEc"
    sheet_id3 = "1OMt07rJLjkT5Eb-y4QKus6e6vcc6N58XQeVOPvzE3uk"
    # sheet_id = "1wpQO-boMtK4_6BeJ7AXP2pdllu3CNwBaQModjuglIt0"
    # sheet_id2 = "1EPvNT5L0a5ZgMFC8P9s5AyFLDCxJL7ETrlJdF2NVIqQ"
    # sheet_id3 = "1Buue4txRSAhy0XlSCpqKqWvzNqvdPucRVbti92aiA5g"

    # List of CSV files and worksheet names
    csv_files = [
        {
            "file": "gpt/mail_sending/results/newsapi_filtered_results.csv",
            "worksheet_name": "newsapi.org",
        },
        {
            "file": "gpt/mail_sending/results_gpt/newsapiai_filtered_results.csv",
            "worksheet_name": "newsapi.ai",
        },
        {
            "file": "gpt/mail_sending/results_gpt/newsdata_filtered_results.csv",
            "worksheet_name": "newsdata",
        },
        {
            "file": "gpt/mail_sending/results_gpt/goperigon_filtered_results.csv",
            "worksheet_name": "perigon",
        },
    ]
    csv_files2 = [
        {
            "file": "mail_sending/results/newsapi_results.csv",
            "worksheet_name": "newsapi.org",
        },
        {
            "file": "mail_sending/results/newsapiai_results.csv",
            "worksheet_name": "newsapi.ai",
        },
        {
            "file": "mail_sending/results/newsdata_results.csv",
            "worksheet_name": "newsdata",
        },
        {
            "file": "mail_sending/results/goperigon_results.csv",
            "worksheet_name": "perigon",
        },
    ]

    csv_files3 = [
        {
            "file": "mail_sending/results/newsapi_filtered_results.csv",
            "worksheet_name": "newsapi.org",
        },
        {
            "file": "mail_sending/results/newsapiai_filtered_results.csv",
            "worksheet_name": "newsapi.ai",
        },
        {
            "file": "mail_sending/results/newsdata_filtered_results.csv",
            "worksheet_name": "newsdata",
        },
        {
            "file": "mail_sending/results/goperigon_filtered_results.csv",
            "worksheet_name": "perigon",
        },
    ]
    # Update the Google Sheet with each file
    for csv_file in csv_files:
        update_google_sheet(sheet_id, csv_file["file"], csv_file["worksheet_name"])

    for csv_file in csv_files2:
        update_google_sheet(sheet_id2, csv_file["file"], csv_file["worksheet_name"])

    for csv_file in csv_files3:
        update_google_sheet(sheet_id3, csv_file["file"], csv_file["worksheet_name"])


update_google_sheets()
