from classes.DawnScraper import DawnScraper
from classes.GeoScraper import GeoScraper
from classes.TheNewsInternationalScraper import TheNewsInternationalScraper
from classes.SamaaScraper import SamaaScraper
from classes.TheNationScraper import TheNationScraper

def main():
    dawn_scraper = DawnScraper()
    geo_scraper = GeoScraper()
    news_international_scraper = TheNewsInternationalScraper()
    samaa_scraper = SamaaScraper()
    the_nation_scraper = TheNationScraper()
    the_nation_scraper.scrape()
    # dawn_scraper.scrape()
    # geo_scraper.scrape()
    # news_international_scraper.scrape()
    # send_cluster_request()
    
main()