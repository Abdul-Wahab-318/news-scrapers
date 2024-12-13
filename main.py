from classes.Scraper import Scraper
from classes.DawnScraper import DawnScraper
from classes.GeoScraper import GeoScraper
from classes.TheNewsInternationalScraper import TheNewsInternationalScraper
from utils.clustering import send_cluster_request

def main():
    dawn_scraper = DawnScraper()
    geo_scraper = GeoScraper()
    news_international_scraper = TheNewsInternationalScraper()
    
    dawn_scraper.scrape()
    geo_scraper.scrape()
    news_international_scraper.scrape()
    send_cluster_request()
    
main()