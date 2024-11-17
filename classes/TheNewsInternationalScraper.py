import re
import time
import os
import re
import schedule
import requests
from Scraper import Scraper
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
import xml.etree.ElementTree as ET

class TheNewsInternationalScraper(Scraper):

    def __init__(self , rss_url , cache_file_name , source='Dawn'):
        self.source = source
        super().__init__( rss_url, cache_file_name)  
        return None
    
    def preprocess_CDATA(self , CDATA):
        description_and_image = BeautifulSoup(CDATA , 'lxml')
        image_tag = description_and_image.find('img')
        image_url = image_tag['src'] if image_tag else None
        
        return  image_url
    
    def extract_articles_from_xml(self , root):
    
        news_articles = []
        try:
            for item in root.findall('.//item'):

                title = item.find('title').text.strip()
                link = item.find('link').text.strip()
                publish_date = self.preprocess_publish_date(item.find('pubDate').text)
                
                description_and_image = item.find('description').text.strip()
                image_url = self.preprocess_img_url(description_and_image)
                
                news_articles.append({
                    "title":title , 
                    "link" :link , 
                    "publish_date":publish_date ,
                    "scraped_date": datetime.now(),
                    "source": "THE NEWS INTERNATIONAL" , 
                    "image_url" : image_url,
                    })
                
        except Exception as e:
            print("Error extracting xml : "  , e)
        return news_articles
    
    def extract_content(self , page):
    
        try:
            content_area = page.find('div' , class_="story-detail")
            content_area_paragraphs = content_area.findAll('p')
            content_area_text = [ paragraph.text for paragraph in content_area_paragraphs]
            content_area_text = " ".join(content_area_text)
            content_area_text = content_area_text.replace('\xa0' , " ")
            
        except Exception as e:
            print("Unknown Error during HTML parsing : " , e)
            return None
            
        return content_area_text
    
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
        
            #self.save_articles(scraped_news_articles)      
            #self.cache_articles(news_articles)
            
        except Exception as e:
            print("Unknown Error : " , e)


news_scraper = TheNewsInternationalScraper("https://www.thenews.com.pk/rss/1/1" , "the_news_international_cache.txt")
news_scraper.scrape()