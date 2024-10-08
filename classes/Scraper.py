
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

    def get_xml_root(self , url):
        response = requests.get(url)
        
        if(response.status_code == 200):
            xml_content = response.text
            return ET.fromstring(xml_content)
        else:
            print("could not fetch xml file : " , response.status_code)
            return None

    def preprocess_publish_date(self , date):
        date_format = "%a, %d %b %Y %H:%M:%S %z"
        parsed_date = datetime.strptime(date , date_format)

        return parsed_date

    def preprocess_description(self , description):
        description = description.strip()
        description_cleaned = re.sub(r'&mdash;|<p>|</p>|<p class="">', ' ', description)
        
        return description_cleaned

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
    
    def extract_xml(self , root):
    
        news_articles = []
        for item in root[0].iter('item'):
            title = item[0].text.strip()
            link = item[1].text
            publish_date = self.preprocess_publish_date(item[2].text)

            description_and_image = item[4].text.strip().split("\n")
            image_url = self.preprocess_img_url(description_and_image[0])
            description = self.preprocess_description(description_and_image[1])
            
            news_articles.append({"title":title , 
                                "link" :link , 
                                "image_url" : image_url ,
                                "publish_date":publish_date ,
                                "scraped_date": datetime.now(),
                                "source": 'Unknown' , 
                                "description":description })
            
        return news_articles

    def extract_content(self , page):
        
        try:
            
            content_area = page.find('div' , class_="content-area")

            if(not content_area):
                content_area = page.find('div' , class_="long-content")

            content_area_paragraphs = content_area.findAll('p')
            content_area_text = [ paragraph.text for paragraph in content_area_paragraphs]
            content_area_text = " ".join(content_area_text)
            content_area_text = content_area_text.replace('\xa0' , " ")
            
        except Exception as e:
            print("Unknown Error scraping : " , e)
            return None
            
        return content_area_text

    def cache_articles(self , articles):
        
        with open(os.path.abspath(self.cache_path) , 'w') as file:
            for article in articles:
                file.write(article["title"] + '\n')

    def scrape_article_content(self , news_articles):
        
        for news in news_articles:
            url = news["link"]
            print(url)
            page = requests.get(url)
            page_scraped = BeautifulSoup(page.text , "html.parser")
            scraped_content = self.extract_content(page_scraped)
            news["content"] = scraped_content

            time.sleep(5)

        return news_articles

    def save_articles(self , articles):
    
        client = MongoClient(self.db_uri)
        
        if(len(articles) == 0):
            print('No articles to insert')
            return
        
        try:
            database = client.get_database("neutra_news")
            news_articles = database.get_collection("news_articles")

            result = news_articles.insert_many(articles)

            print("Articles inserted : " , len(result.inserted_ids))

            client.close()

        except Exception as e:
            raise Exception("Unable to find the document due to the following error: ", e)
              
    def scrape(self):
        try:
            xml_root = self.get_xml_root(self.rss_url)

            news_articles = self.extract_xml(xml_root)
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
            
            
