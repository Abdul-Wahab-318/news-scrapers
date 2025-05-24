from abc import ABC , abstractmethod
from playwright.sync_api import sync_playwright
from classes.Scraper import Scraper
from bs4 import BeautifulSoup
import time

class PlaywrightScrapper(ABC , Scraper):
    
    def __init__(self , rss_url , source):
        super().__init__(rss_url , source)
        return None
    
    def get_html_page(self):
        
        try:
            print("GETTING HTML  PAGE......")
            with sync_playwright() as playwright:
                
                browser = playwright.chromium.launch(headless=False)
                context =  browser.new_context()
                page =  context.new_page()
                
                page.goto(self.rss_url , timeout=10000)
                page.wait_for_selector("body", timeout=10000)
                html_content = page.content()
                
                browser.close()
            
            html_content = BeautifulSoup(html_content , 'html.parser')
            return html_content
            
        except Exception as e:
            print("ERROR : Error getting HTML page ")
            print(e)
            return None

    def scrape_article_content(self , news_articles , parse_html_content):
        try:
            with sync_playwright() as playwright:
                
                articles = []
                browser = playwright.chromium.launch(headless=False)
                context = browser.new_context()
                page = browser.new_page()
                
                for article in news_articles:
                    
                    try:
                        
                        page.goto(article['link'] , timeout=10000)
                        page.wait_for_selector("#content" , timeout=10000) # wait for main content div
                        page_content = page.query_selector("article.single-article").inner_html()
                        page_content = BeautifulSoup(page_content , 'html.parser')
                        
                        article_contents = parse_html_content(page_content)
                        articles.append({
                            **article,
                            **article_contents
                        })
                        time.sleep(4)
                    
                    except Exception as e:
                        print("Error scraping article : " , article['link'])
                        print(e)
                        
                return articles
                    
        except Exception as e:
            print(f"ERROR : error scraping articles in scrape_article_content , source : {self.source}")
            raise Exception(f"ERROR : error scraping articles in scrape_article_content , source : {self.source}")

    @abstractmethod
    def scrape(self):
        pass