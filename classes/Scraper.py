
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime , timedelta
import re
import time
import warnings
import spacy
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_HOST = os.getenv('REDIS_HOST')
MONGODB_URI = os.getenv('MONGODB_URI')

class Scraper:

    def __init__(self , rss_url , source ):
        self.source = source
        self.cache_key = f'{source}_articles'
        self.rss_url = rss_url
        self.dbClient = MongoClient(MONGODB_URI)
        self.nlp = spacy.load("en_core_web_trf" , disable=['tagger' , 'parser' , 'lemmatizer'])
        return None

    def clean_text(self , text):
        return re.sub(r'[\x00-\x1F\x7F]|[^\x20-\x7E]|\s+', ' ', text)
    
    def get_xml_root(self , url , retries=3 , delay=1):
        
        for attempt in range(1, retries+1):
            try:
                response = requests.get(url)
                
                if(response.status_code == 200):
                    xml_content = response.text
                    return ET.fromstring(xml_content)
                else:
                    print(f"Attempt {attempt}: Failed to fetch XML file - Status code {response.status_code}")
                    if(attempt < retries):
                        time.sleep(delay)
                    else:
                        print(f"Attempt {attempt}: Failed to fetch XML file - Status code {response.status_code}")
                        raise Exception(f"HTTP Error while fetching XML file: {response.status_code}")
                
            except Exception as e:
                raise Exception("Failed to fetch XML file")
                
    def preprocess_publish_date(self , date):
        date_format = "%a, %d %b %Y %H:%M:%S %z"
        parsed_date = datetime.strptime(date , date_format)

        return parsed_date

    def preprocess_img_url(self , img_url):
        try:            
            bs4 = BeautifulSoup(img_url , 'lxml')
            image_element = bs4.find('img')
            return image_element['src']
        except Exception as e:
            print("Error processing img url")
            return None         
    
    #disjoint between new and old to filter out duplicates
    def find_disjoint(self , arr1, arr2):
        # Convert arrays to sets
        set1 = set(arr1)
        set2 = set(arr2)
        
        # Find disjoint elements
        disjoint = list(set1.difference(set2))
        return disjoint
    
    def filter_articles(self, articles):

        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(days=1)

        db = self.dbClient.get_database("neutra_news_mid")
        article_collection = db.get_collection("articles")
        
        # Fetch articles scraped in the last 24 hours
        query = {
            'source': self.source,
            "scraped_date": {"$gte": twenty_four_hours_ago}  # Articles scraped in the last 24 hours
        }
        projection = {'link': 1, '_id': 1}

        previous_articles = list(article_collection.find(query, projection))
        previous_links = [article['link'] for article in previous_articles]

        if len(previous_links) == 0:
            return articles

        scraped_links = [article['link'] for article in articles]
        new_titles = self.find_disjoint(scraped_links, previous_links)

        new_articles = [article for article in articles if article["link"] in new_titles]
        return new_articles
    
    def apply_NER(self , articles):
        
        ner_labels = [
        "PERSON",      # People, including fictional
        "NORP",        # Nationalities or religious or political groups
        "FAC",         # Buildings, airports, highways, bridges, etc.
        "ORG",         # Companies, agencies, institutions, etc.
        "GPE",         # Countries, cities, states
        "LOC",         # Non-GPE locations, mountain ranges, bodies of water
        "PRODUCT",     # Objects, vehicles, foods, etc. (Not services)
        "EVENT",       # Named hurricanes, battles, wars, sports events, etc.
        "WORK_OF_ART", # Titles of books, songs, etc.
        "LAW",         # Named documents made into laws
        "LANGUAGE",    # Any named language
        ]

        for article in articles:
            doc = self.nlp(article['title'])
            
            entities = {}
            for ent in doc.ents:
                
                if ( ent.label_ not in ner_labels ): continue
                
                entity_text = ent.text.upper()
                if ent.label_ in entities:
                    entities[ent.label_].append(entity_text)
                else:
                    entities[ent.label_] = [entity_text]
                    
            article['entities'] = entities
                
            # print("Title : " , article['title'])
            # print("entities : " , entities)

        return articles

    #extracts the body for each article and returns the updated articles with body
    #args: news_articles : list of news articles , parse_html_content : function that extracts the body from each article
    def scrape_article_content(self , news_articles , parse_html_content):

        for news in news_articles:
            url = news["link"]
            print("GET:" , url)
            page = requests.get(url)
            page_parsed = BeautifulSoup(page.text , "html.parser")
            article_body = parse_html_content(page_parsed)
            news["content"] = article_body

            time.sleep(5)

        return news_articles

    def save_articles(self , articles):
                
        if(len(articles) == 0):
            print('No articles to insert')
            return
        
        try:
            database = self.dbClient.get_database("neutra_news_mid")
            news_articles = database.get_collection("articles")

            result = news_articles.insert_many(articles)

            print("Articles inserted : " , len(result.inserted_ids))
            self.dbClient.close()
        except Exception as e:
            raise Exception("Unable to find the document due to the following error: ", e)
              
    def scrape(self):
        try:
            xml_root = self.get_xml_root(self.rss_url)

            news_articles = self.extract_articles_from_xml(xml_root)
            latest_news_articles = self.filter_articles(news_articles)
            latest_news_articles = self.apply_NER(latest_news_articles)
            scraped_news_articles = self.scrape_article_content(latest_news_articles)
    
            print("prev : " , len(news_articles))
            print("new : " , len(latest_news_articles))
            print('Time : ' , datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
        
            self.save_articles(scraped_news_articles)      
            
        except Exception as e:
            print("Unknown Error : " , e)
            
            
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.*")