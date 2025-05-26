from classes.Scraper import Scraper
from datetime import datetime , timezone
from bs4 import BeautifulSoup
import requests
import time
import json
import re

class TheNationScraper(Scraper):

    def __init__(self , rss_url="https://www.nation.com.pk/national" , source='The_Nation'):
        super().__init__( rss_url, source )  
        return None
    
    def get_html_page(self , url , retries=3 , delay=1):
    
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        for attempt in range(1, retries+1):
            try:
                response = requests.get(url , headers=headers)
                if(response.status_code == 200):
                    html_text = response.text
                    return html_text
                else:
                    print(f"Attempt {attempt}: Failed to fetch HTML file - Status code {response.status_code}")
                    print(response)
                    if(attempt < retries):
                        time.sleep(delay)
                    else:
                        print(f"Attempt {attempt}: Failed to fetch HTML file - Status code {response.status_code}")
                        raise Exception(f"HTTP Error while fetching HTML file: {response.status_code}")
                
            except Exception as e:
                raise Exception("Failed to fetch HTML file")
    
    def extract_article_links_main_page(self , page):
    
        news_articles = []
        now = datetime.now(timezone.utc)
        page = BeautifulSoup(page , 'html.parser')
        
        articles_block = page.find("div" , class_ = "jeg_posts jeg_load_more")
        for article in articles_block.children:
            
            if( article.name != 'article' ): # if tag type is not article
                continue
            
            title = article.select_one("div h3 a").text if article.select_one("div h3 a") is not None else None
            link = article.select_one("div h3 a")['href'] if article.select_one("div h3 a") is not None else None
            
            published_date = article.find("div" , class_="jeg_meta_date").text.strip() if article.find("div",class_="jeg_meta_date") else datetime.now()
            published_date = self.preprocess_publish_date(published_date)
            
            img_tag = article.find("div" , class_="top-center lazyautosizes lazyloaded wp-post-image")
            
            if(img_tag):
                img_tag_style = img_tag.get("style")
                match = re.search(r'url\((.*?)\)', img_tag_style)
                image_url = match.group(1) if match else None
            
            news_articles.append({
                "title" : title ,
                "link" : link ,
                "source" : self.source,
                "image_url" : image_url,
                "news_category" : "pakistan" ,
                "scraped_date" : datetime.now(),
                "published_date" : published_date,
                "status" : "scraped",
                "clicks" : 0,
                "blindspot" : False
            })
                
        return news_articles
    
    def parse_html_content(self , page):
    
        try:
            content_area = page.find('div' , class_="news-detail-content-class")
            content_area_paragraphs = content_area.find_all('p')
            content_area_text = [ paragraph.text + "\n\n" for paragraph in content_area_paragraphs]
            content_area_text = " ".join(content_area_text)
            content_area_text = self.clean_text(content_area_text)
            
        except Exception as e:
            print("Unknown Error during HTML parsing : " , e)
            return None
            
        return content_area_text
    
    def preprocess_publish_date(self , date):
        try:
            parsed_date = datetime.strptime(date, "%I:%M %p | %B %d, %Y")
            return parsed_date
        except Exception as e:
            print("Failed to parse publish date : " , e)
            return datetime.now()
    
    def scrape(self):
        try:
            print("Scraping " , self.source , " : \n") 
            html_page = self.get_html_page(self.rss_url)

            news_articles = self.extract_article_links_main_page(html_page)
            latest_news_articles = self.filter_articles(news_articles)
            latest_news_articles = self.apply_NER(latest_news_articles)
            scraped_news_articles = self.scrape_article_content(latest_news_articles , self.parse_html_content)

            self.save_articles(scraped_news_articles)      
            print('Time : ' , datetime.now().strftime("%A, %B %d, %Y %I:%M %p"))
            print("\n\n")
            
        except Exception as e:
            print(f"Error Scraping {self.source} : " , e)
