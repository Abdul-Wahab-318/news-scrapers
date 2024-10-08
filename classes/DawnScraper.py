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

class DawnScraper(Scraper):

    def __init__(self , rss_url , cache_file_name , source='Dawn'):
        self.source = source
        super().__init__( rss_url, cache_file_name)  
        return None

    def preprocess_description(self , description):
        html = BeautifulSoup(description , 'lxml')
        description = html.get_text().strip().replace('\n' ,' ')
        
        return description

    def extract_xml(self , root):
    
        news_articles = []
        namespaces = {'media': 'http://search.yahoo.com/mrss/'}
            
        for item in root.findall('.//item'):
            
            title = item.find('title').text.strip()
            title = re.sub(r'[‘’]', '\'', title)
            link = item.find('link').text.strip()
            description = self.preprocess_description(item.find('description').text)
            category = item.find('category').text.strip()
            publish_date = self.preprocess_publish_date(item.find('pubDate').text)
            image_url = item.find('media:content', namespaces)#.get('url')
            
            if(category != 'Pakistan'):
                continue
            
            if(image_url):
                image_url = image_url.get('url')
            else:
                image_url = None
            
            print(link)
            
            news_articles.append({"title":title , 
                                "link" :link , 
                                "publish_date":publish_date ,
                                "scraped_date": datetime.now(),
                                "source": "DAWN" , 
                                "image_url" : image_url,
                                "content":description })
            
        return news_articles

    def scrape(self):
        
        xml_root = self.get_xml_root(self.rss_url)
        
        news_articles = self.extract_xml(xml_root)
        latest_news_articles = self.filter_articles(news_articles)
        latest_news_articles = self.apply_NER(latest_news_articles)
        
        self.save_articles(latest_news_articles)
        self.cache_articles(news_articles)
        
        print("prev : " , len(news_articles))
        print("new : " , len(latest_news_articles))
        print('Time : ' , datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
            
            
geo_scraper = DawnScraper("https://www.dawn.com/feeds/home" , "dawn_cache.txt")
geo_scraper.scrape()
