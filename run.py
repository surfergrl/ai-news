import requests
from bs4 import BeautifulSoup
from googlesearch import search
from transformers import pipeline
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Configuration
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_specific_password"  # Use an app-specific password for Gmail
RECIPIENTS = ["recipient1@example.com", "recipient2@example.com"]
SEARCH_QUERY = "AI news today site:*.edu | site:*.org | site:*.gov -inurl:(signup | login)"

# Initialize summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def get_top_articles(query, num_results=5):
    articles = []
    today = datetime.now().strftime("%Y-%m-%d")
    for url in search(query, num_results=num_results, stop=num_results):
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "No title available"
            
            # Extract thumbnail (first image with reasonable size)
            img = soup.find('img', width=lambda x: int(x or 0) > 100 if x else False)
            thumbnail = img['src'] if img and img.get('src') else "No image available"
            if thumbnail.startswith('/'):
                thumbnail = url + thumbnail
            
            # Extract content for summary
            paragraphs = soup.find_all('p')
            content = ' '.join(p.get_text() for p in paragraphs[:5])[:1000]  # Limit to first 5 paragraphs
            
            # Summarize
            if content:
                summary = summarizer(content, max_length=60, min_length=30, do_sample=False)[0]['summary_text']
            else:
                summary = "Summary not available."
            
            articles.append({
                'title': title,
                'url': url,
                'thumbnail': thumbnail,
                'summary': summary
            })
        except Exception as e:
            print(f"Error processing {url}: {e}")
    return articles

def send_email(articles):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = ", ".join(RECIPIENTS)
    msg['Subject'] = f"Top AI News Articles - {datetime.now().strftime('%Y-%m-%d')}"

    body = "<h2>Today's Top AI News</h2>"
    for article in articles:
        body += f"""
        <h3>{article['title']}</h3>
        <p><img src="{article['thumbnail']}" width="100" height="100" onerror="this.src='https://via.placeholder.com/100'"></p>
        <p><a href="{article['url']}">{article['url']}</a></p>
        <p>{article['summary']}</p>
        <hr>
        """
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
    print("Fetching today's AI news...")
    articles = get_top_articles(SEARCH_QUERY)
    if articles:
        print("Sending email...")
        send_email(articles)
        print("Email sent successfully!")
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()