"""
Main module for chat and automation tools.
Contains classes for conversation management, LLM interactions, file operations, and various utilities.
"""

# Standard library imports
import json
import os
import re
from utils.logger_config import setup_logger
from utils.config import default_model

# Third-party imports
import requests
# from crewai_tools import DallETool
from dotenv import load_dotenv
import logging


# Get the logger 
setup_logger()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

import re

class Search:
    """Utils for web searching and content retrieval."""
    @staticmethod
    def optimize_query(query: str) -> str:
        """
        Optimizes the search query by removing common stop words and phrases.
        """
        prompt=f"""Example of research:
Provide a comprehensive overview of mindtrip.ai, including its founding, mission, and business model.

Example of search query that maximizes the results for this research:
("mindtrip.ai" OR "mindtrip ai" OR "mind trip ai") (founder OR founded OR mission OR "business model" OR startup OR investment OR funding)

Based on the examples above, provide a search query that maximizes the results for this research : {query}

Your response must be is json:
{{"query":"<your proposed query>"}}

Your response must start with {{"""
        response = default_model.invoke(prompt)
        query_json=response.content.strip()

        query_json=query_json.replace("```json","").replace("```","")
        # logger.debug(f"Query json: {query_json}")
        optimized_query=json.loads(query_json)["query"]
        # logger.debug(f"Optimized search query: {response}") 
        optimized_query=optimized_query.replace("'", "\"")
        return optimized_query

    @staticmethod
    def _get_tbs(time_range: str) -> str:
        """
        Generates the 'tbs' parameter for the Serper API based on the given time range.

        Args:
            time_range: A string representing the desired time range. 
                        Supported formats: 'h', 'd', 'w', 'm', 'y', or any of these 
                        with a number before it (e.g., '10y', '5m').

        Returns:
            A string representing the 'tbs' parameter value.
        """
        match = re.match(r"(\d*)([hdwmy])", time_range)
        if match:
            amount, unit = match.groups()
            amount = amount if amount else "1"  # Default to 1 if no number is given
            return f"qdr:{amount}{unit}"
        else:
            raise ValueError(f"Invalid time_range format: {time_range}")
            
    @staticmethod
    def search_instagram(query: str, limit: int = 10, time_range: str = "24h") -> str:
        """Search Instagram for content."""
        return Search.search(f"site:instagram.com {query}", limit, time_range)

    @staticmethod
    def search_twitter(query: str, limit: int = 10, time_range: str = "24h") -> str:
        """Search Twitter for content."""
        return Search.search(f"site:x.com {query}", limit, time_range)

    @staticmethod
    def search(_query: str, limit: int = 10, time_range: str = "24h") -> str:
        """
        General web search functionality.
        
        Args:
            query: Search query
            limit: Maximum number of results
            time_range: Time range for search
            
        Returns:
            Formatted search results
        """
        logger.debug(f"Starting search for '{_query}' with limit {limit} and time range {time_range}")

        query=Search.optimize_query(_query)
        logger.debug(f"Optimized search query: {query} -inurl:pdf")

        url = "https://google.serper.dev/search"
        payload = json.dumps({
            'q': query,
            'num': limit #put limit to accept the requestors limit
        })
        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        logger.debug(f"Search API call Response: {response.text}")
        results = response.json().get('organic', [])
        logger.debug(f"Results: {results}")
        
        formatted_results = []
        for result in results:
            # Only add the link if it exists and is not empty
            if 'link' in result and result['link']:
                formatted_results.append(result["link"])
        
        # Check if we have any valid results
        if not formatted_results and 'organic' in response.json():
            logger.warning(f"No valid links found in search results. Raw results: {response.json()['organic']}")
        
        logger.debug(f"Formatted results: {formatted_results}")
        logger.debug("Search is done")
        return formatted_results

    @staticmethod
    def search_news(_query: str, limit: int = 5, time_range: str = "24h") -> str:
        """
        Util for Search news articles.
        
        Args:
            query: Search query
            limit: Maximum number of results
            time_range: Time range for search
            
        Returns:
            Formatted news results
        """
        query=Search.optimize_query(_query)
        url = "https://google.serper.dev/news"
        payload = json.dumps({
            "q": query,
            "num": 20, #put limit to respect the requestors limit
            "tbs": Search._get_tbs(time_range)
        })
        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        results = response.json().get('news', [])
        
        formatted_results = []
        for result in results:
            # Only add the link if it exists and is not empty
            if 'link' in result and result['link']:
                formatted_results.append(result['link'])
        
        # Check if we have any valid results
        if not formatted_results and 'news' in response.json():
            logger.warning(f"No valid links found in news results. Raw results: {response.json()['news']}")
            
        return formatted_results

    @staticmethod
    def get_relevant_sites(query: str) -> tuple:
        """
        Gets relevant sites to search across and appropriate time range for a given query.
        
        Args:
            query (str): The search query to find relevant sites for
            
        Returns:
            tuple: (str, str) containing:
                - Space-separated string of relevant sites formatted for search
                - Time range in Google search notation (e.g., 'h', 'd', 'w', 'm', 'y')
        """
        sites_prompt = f"""Given this search query: "{query}", provide:
        1. 15 most relevant domains to search across (including major news sites, specialized industry sites, and authoritative sources)
        2. The most appropriate time range for this query (considering how often this type of information changes)

        Response must be in JSON format:
        {{
            "sites": ["domain1.com", "domain2.com", ...],
            "time_range": "<time_range>"
        }}

        For time_range, use these formats:
        - "h" for last hour (breaking news, live events)
        - "d" for last 24 hours (recent news)
        - "w" for last week (recent developments)
        - "m" for last month (recent trends)
        - "y" for last year (established information)
        - "5y" for last 5 years (historical information)

        Only include domain names without 'www.' or 'https://'.
        Your response must start with {{"""

        sites_response = default_model.invoke(sites_prompt)
        sites_response=sites_response.content.strip()
        logger.debug(f"Sites response: {sites_response}")
        sites_response=sites_response.replace("```json","").replace("```","")
        response_json = json.loads(sites_response)
        
        # Convert list of sites to space-separated string
        sites_string = " site:" + " site:".join(response_json["sites"])
        
        return sites_string, response_json["time_range"]

    # def search(self, query: str, limit: int = 5, time_range: str = None) -> list:
    #     """
    #     Performs a search with the given query and parameters.
        
    #     Args:
    #         query (str): The search query
    #         limit (int, optional): Maximum number of results. Defaults to 5.
    #         time_range (str, optional): Time range for results. If None, will be determined automatically.
            
    #     Returns:
    #         list: Search results
    #     """
    #     relevant_sites, suggested_time_range = self.get_relevant_sites(query)
    #     enhanced_query = f"{query} {relevant_sites}"
        
    #     # Use provided time_range if specified, otherwise use suggested_time_range
    #     final_time_range = time_range or suggested_time_range
        
    #     # Perform the actual search with the enhanced query
    #     return self._execute_search(enhanced_query, limit, final_time_range)



def main():
    """Main execution function."""
    Search.search(query="Ilan Twig", limit=5, time_range="d")
    exit()
    logger.debug("---------------------------------------------------------------------")
    logger.debug("Testing file operations...")
    File.test_write_and_read_tweets()
    logger.debug("---------------------------------------------------------------------")

if __name__ == "__main__":
    main()
