
import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from bs4 import BeautifulSoup
import time
import os
import schedule
from pymongo import MongoClient
import spacy

MONGODB_URI='mongodb://localhost:27017/'
URL='https://feeds.feedburner.com/geo/GiKR'
class Scraper:

    def __init__(self , rss_url , cache_file_name ):
        
        self.cache_path = os.path.abspath('cache\\' + cache_file_name)
        self.db_uri = "mongodb://localhost:27017/"
        self.rss_url = rss_url
        self.nlp = spacy.load("en_core_web_trf" , disable=['tagger' , 'parser' , 'lemmatizer'])
        return None

    def get_xml_root(self , url , retries=3 , delay=2):
        
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
    
    def find_disjoint(self , arr1, arr2):
        # Convert arrays to sets
        set1 = set(arr1)
        set2 = set(arr2)
        
        # Find disjoint elements
        disjoint = set1.difference(set2)
        print("disjoint : " , set1.difference(set2) )
        #  convert to list
        disjoint = list(disjoint)
        
        return disjoint
    
    def filter_articles(self , articles):
        try:
            
            current_titles = [ article['title'] for article in articles ]
            
            with open(os.path.abspath(self.cache_path) , 'r') as file:
                prev_titles = file.readlines()
                prev_titles = [ title.strip() for title in prev_titles ]
        
            current_titles = self.find_disjoint(current_titles , prev_titles)
            
        except FileNotFoundError as e:
            print(f"Error: {e}")
        
        articles = [ article for article in articles if article["title"] in current_titles ]
        
        return articles
    
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
                
            print("Title : " , article['title'])
            print("entities : " , entities)
            print("\n\n")
        return articles

    def cache_articles(self , articles):
        
        with open(os.path.abspath(self.cache_path) , 'w') as file:
            for article in articles:
                file.write(article["title"] + '\n')

    #extracts the body for each article and returns the updated articles with body
    #args: news_articles : list of news articles , parse_html_content : function that extracts the body from each article
    def scrape_article_content(self , news_articles , parse_html_content ):

        for news in news_articles:
            url = news["link"]
            print(url)
            page = requests.get(url)
            page_parsed = BeautifulSoup(page.text , "html.parser")
            article_body = parse_html_content(page_parsed)
            news["content"] = article_body

            time.sleep(5)

        return news_articles

    def save_articles(self , articles):
    
        client = MongoClient(self.db_uri)
        
        if(len(articles) == 0):
            print('No articles to insert')
            return
        
        try:
            database = client.get_database("neutra_news_mid")
            news_articles = database.get_collection("news_articles")

            result = news_articles.insert_many(articles)

            print("Articles inserted : " , len(result.inserted_ids))

            client.close()

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
            self.cache_articles(news_articles)
            
        except Exception as e:
            print("Unknown Error : " , e)
            
            
