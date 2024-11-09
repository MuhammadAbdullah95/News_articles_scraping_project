import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import re

# Define category URLs
CATEGORY_URLS = {
    "World": "https://www.bbc.com/news/world",
    "Business": "https://www.bbc.com/news/business",
    "Technology": "https://www.bbc.com/news/technology",
    "Artificial intelligence": "https://www.bbc.com/innovation/artificial-intelligence",
    "Innovation": "https://www.bbc.com/innovation",
    "Travel": "https://www.bbc.com/travel",
    "Culture": "https://www.bbc.com/culture",
    "Arts": "https://www.bbc.com/arts",
    "Earth": "https://www.bbc.com/future-planet",
    "Science": "https://www.bbc.com/innovation/science",
}


# Function to scrape a specific category
def scrape_bbc_category(category_name, category_url):
    response = requests.get(category_url)
    soup = BeautifulSoup(response.content, "html.parser")

    articles = []
    titles_seen = set()  # Track unique titles to avoid duplicates

    # Find all articles in the category page
    news_items = soup.find_all(
        ["article", "div"], attrs={"data-testid": re.compile(r".*")}
    )

    for item in news_items:
        # Extract the title
        title_tag = item.find(["h3", "h2"])
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title in titles_seen:
                continue
            titles_seen.add(title)
        else:
            continue

        # Extract the summary
        summary_tag = item.find("p")
        summary = (
            summary_tag.get_text(strip=True) if summary_tag else "No summary available"
        )

        # Extract publication date if available
        date_tag = item.find("span", attrs={"data-testid": "card-metadata-lastupdated"})
        if date_tag:
            date_text = date_tag.get_text(strip=True)
            if "hrs ago" in date_text:
                hours = int(re.search(r"(\d+)", date_text).group(1))
                publication_date = datetime.now() - timedelta(hours=hours)
            elif "mins ago" in date_text:
                minutes = int(re.search(r"(\d+)", date_text).group(1))
                publication_date = datetime.now() - timedelta(minutes=minutes)
            else:
                publication_date = "Unknown date"
        else:
            publication_date = "Unknown date"

        # Extract the link
        link_tag = item.find("a", href=True)
        link = (
            "https://www.bbc.com" + link_tag["href"]
            if link_tag
            else "No link available"
        )

        # Format the date for consistency
        if isinstance(publication_date, datetime):
            publication_date = publication_date.strftime("%Y-%m-%d %H:%M:%S")

        articles.append(
            {
                "title": title,
                "date": publication_date,
                "summary": summary,
                "link": link,
                "category": category_name,
            }
        )

    return articles


# Function to scrape all categories
def scrape_bbc_news():
    all_articles = []
    for category_name, category_url in CATEGORY_URLS.items():
        all_articles.extend(scrape_bbc_category(category_name, category_url))
    return pd.DataFrame(all_articles)


# Scrape the data
news_df = scrape_bbc_news()

# Convert date to datetime for filtering
news_df["date"] = pd.to_datetime(news_df["date"], errors="coerce")

# Streamlit App
st.title("BBC News Dashboard")
st.write("Explore the latest news articles from BBC with real-time updates.")

# Date Filter
st.sidebar.header("Filter News")
date_filter = st.sidebar.selectbox(
    "Show articles from the last:", options=["All", "24 hours", "48 hours", "7 days"]
)

if date_filter == "24 hours":
    cutoff = datetime.now() - timedelta(hours=24)
    news_df = news_df[news_df["date"] >= cutoff]
elif date_filter == "48 hours":
    cutoff = datetime.now() - timedelta(hours=48)
    news_df = news_df[news_df["date"] >= cutoff]
elif date_filter == "7 days":
    cutoff = datetime.now() - timedelta(days=7)
    news_df = news_df[news_df["date"] >= cutoff]

# Category Filter
category_filter = st.sidebar.multiselect(
    "Select categories", options=list(CATEGORY_URLS.keys())
)

if category_filter:
    news_df = news_df[news_df["category"].isin(category_filter)]

# Display Articles
st.subheader("Latest BBC News Articles")
for idx, row in news_df.iterrows():
    st.write(f"### {row['title']}")
    st.write(
        f"**Published on:** {row['date'].strftime('%Y-%m-%d %H:%M') if not pd.isnull(row['date']) else 'Unknown date'}"
    )
    st.write(f"{row['summary']}")
    st.write(f"[Read more]({row['link']})")  # Display link as a clickable text
    st.write(f"**Category:** {row['category']}")
    st.write("---")
