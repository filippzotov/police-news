import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(sender_email, app_password, recipient_email, subject, body):
    """
    Sends an email using Gmail's SMTP server.

    :param sender_email: Gmail address of the sender
    :param app_password: Generated App Password for the sender's Gmail
    :param recipient_email: Recipient's email address
    :param subject: Subject of the email
    :param body: Body of the email
    """
    # Gmail SMTP server configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade to secure connection
            server.login(sender_email, app_password)  # Login with App Password
            server.send_message(msg)  # Send the email
        print(f"Email successfully sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def read_titles_and_urls_from_csv(filename):
    """
    Reads titles and URLs from a CSV file and returns them as a formatted string.

    :param filename: The name of the CSV file
    :return: A formatted string of titles and URLs
    """
    articles = []
    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = row.get("Title", "N/A")
                url = row.get("URL", "N/A")
                articles.append(f"- {title}\n  {url}")
    except FileNotFoundError:
        return "No articles found."

    if not articles:
        return "No articles available in the file."

    return "\n\n".join(articles)


def get_perigon_text(filename):
    """
    Reads titles and URLs from a CSV file and returns them as a formatted string.

    :param filename: The name of the CSV file
    :return: A formatted string of titles and URLs
    """
    articles = []
    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                title = row.get("Title", "N/A")
                date = row.get("Published Date", "N/A")
                url = row.get("URL", "N/A")
                articles.append(f"- {title} - {date}\n  {url}")
    except FileNotFoundError:
        return "No articles found."

    if not articles:
        return "No articles available in the file."

    return "\n\n".join(articles)


import os


def send_articles_via_email():
    # Test email credentials
    sender_email = "cameron.news.project@gmail.com"  # Replace with your Gmail address
    app_password = "fbmg ebiv ziwu elxc"  # Replace with the generated App Password
    recipient_email = (
        "cameron.news.project@gmail.com"  # Replace with the recipient's email address
    )
    # Email content
    filenames = [
        "gpt/mail_sending/results/newsapi_filtered_results.csv",
        "gpt/mail_sending/results_gpt/newsapiai_filtered_results.csv",
        "gpt/mail_sending/results_gpt/newsdata_filtered_results.csv",
        "gpt/mail_sending/results_gpt/goperigon_filtered_results.csv",
    ]
    api_names = ["NewsAPI.org", "NewsAPI.AI", "NewsData", "Perigon"]
    for filename, api_name in zip(filenames, api_names):
        if not os.path.exists(filename):
            continue
        subject = f"Daily News Articles from {api_name}"
        body = f"\n\n{get_perigon_text(filename)}"
        send_email(sender_email, app_password, recipient_email, subject, body)

    # Call the function to send the email
    # send_email(sender_email, app_password, recipient_email, subject, body)


if __name__ == "__main__":
    send_articles_via_email()
