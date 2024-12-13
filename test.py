
from pymongo import MongoClient
from datetime import datetime , timedelta
from dotenv import load_dotenv
import os

MONGODB_URI = os.getenv('MONGODB_URI')
dbClient = MongoClient(MONGODB_URI)
def filter_articles(articles):

    now = datetime.today()
    twenty_four_hours_ago = (now - timedelta(days=1))
    year = twenty_four_hours_ago.year
    month = twenty_four_hours_ago.month
    day = twenty_four_hours_ago.day

    yesterday = datetime(year,month,day)

    print(yesterday)

    db = dbClient.get_database("neutra_news_mid")
    article_collection = db.get_collection("articles")
    
    # Fetch articles scraped in the last 24 hours
    query = {
        'source': 'Dawn',
        "scraped_date": {"$lte": twenty_four_hours_ago}  # Articles scraped in the last 24 hours
    }
    projection = {'link': 1, '_id': 1 , 'scraped_date': 1}

    previous_articles = list(article_collection.find(query, projection))
    previous_links = [article['link'] for article in previous_articles]
    print("Previous articles:", len(previous_links))
    print(previous_articles)
    
    if len(previous_links) == 0:
        return articles

    return 0

filter_articles([])

