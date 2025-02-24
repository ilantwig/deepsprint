from utils.capabilities.Text import TextUtils
from utils.capabilities.Search import logger


from crewai_tools import ScrapeWebsiteTool
# from crewai_tools import SeleniumScrapingTool

# To enable scrapping any website it finds during it's execution
tool = ScrapeWebsiteTool()
# selenium_tool = SeleniumScrapingTool()
counter:int=0
sites_scrapped:list[str]=[]

class Browser:
    def get_stats()->str:
        global sites_scrapped
        global counter
        return f"Scraped {counter}\nsites: {sites_scrapped} "
    
    def scrape_and_summarize_web_page(url: str) -> str:
        """
        Open a url and return a detailed summary of its content.
        """
        global counter
        global sites_scrapped
        sites_scrapped.append(url)
        counter+=1
        logger.debug(f"Scraping number {counter}: Attempting to open URL: {url}")
        # text=selenium_tool._run(website_url=url)
        text=tool._run(website_url=url)
        # logger.debug(f"Raw scraping: {text}")
        summarized_text = TextUtils.perform_task(text, "Create a detailed summary of the provided content. Do not miss out on any fact/detail. Keep links, dates in tact.")
        logger.debug(f"Summarized text final length: {len(summarized_text)} characters")
        logger.debug(f"\\nn--------------------------------------------------\nSummary: {summarized_text}\n---------------------------\n\n")

        return summarized_text.replace("'","&#39;")