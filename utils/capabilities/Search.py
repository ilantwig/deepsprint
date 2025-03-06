"""
Main module for chat and automation tools.
Contains classes for conversation management, LLM interactions, file operations, and various utilities.
"""

# Standard library imports
from datetime import datetime
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
from utils.crewid import CrewID
from utils.capabilities.File import File


# Get the logger 
setup_logger()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

import re

class Search:
    """Utils for web searching and content retrieval."""
    
    @staticmethod
    def _save_search_log(query, optimized_query=None, blend_ratio=None, results=None, search_type="standard", file_path=None):
        """
        Saves search decisions and results to a text file.
        
        Args:
            query: Original search query
            optimized_query: Optimized version of the query (if available)
            blend_ratio: Dictionary of blend ratios (if applicable)
            results: List of search results (can include dictionaries with scores or simple URLs)
            search_type: Type of search performed (e.g., "standard", "smart", "blended")
            file_path: Path to the log file (if None, will use the crew ID directory)
        """
        # Get the current crew ID
        crewid = CrewID.get_crewid()
        
        # Create the output directory path
        if file_path is None:
            output_dir = os.path.join("output", crewid)
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, "search_logs.txt")
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"SEARCH LOG - {search_type.upper()} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Original Query: {query}\n")
            
            if optimized_query:
                f.write(f"Optimized Query: {optimized_query}\n")
                
            if blend_ratio:
                f.write(f"Blend Ratio: {blend_ratio}\n")
                
            f.write(f"\nRESULTS:\n{'-'*40}\n")
            
            if results:
                for i, result in enumerate(results, 1):
                    if isinstance(result, dict) and 'link' in result:
                        # For smart search with scored results
                        f.write(f"{i}. {result['link']}\n")
                        if 'score' in result:
                            f.write(f"   Score: {result['score']:.2f}\n")
                        if 'title' in result and result['title']:
                            f.write(f"   Title: {result['title']}\n")
                        if 'snippet' in result and result['snippet']:
                            f.write(f"   Snippet: {result['snippet'][:100]}...\n")
                    else:
                        # For simple URL results
                        f.write(f"{i}. {result}\n")
                    f.write(f"{'-'*40}\n")
            else:
                f.write("No results found.\n")
                
            f.write("\n\n")
            
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

        # Save the search optimization prompt
        crewid = CrewID.get_crewid()
        File.save_prompt(crewid, "search_optimization", prompt)
        
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
        
        # Log search results to file
        Search._save_search_log(_query, query, results=formatted_results, search_type="standard")
        
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
    def smart_search(query: str, limit: int = 10, time_range: str = "24h") -> list:
        """
        Enhanced search functionality that optimizes for higher accuracy results.
        
        Args:
            query: Search query
            limit: Maximum number of results
            time_range: Time range for search
            
        Returns:
            Formatted search results with higher accuracy
        """
        logger.debug(f"Starting smart search for '{query}' with limit {limit} and time range {time_range}")
        
        # Step 1: Optimize the query
        optimized_query = query#Search.optimize_query(query)
        logger.debug(f"Optimized search query: {optimized_query}")
        
        # # Step 2: Get relevant sites and appropriate time range
        # relevant_sites, suggested_time_range = Search.get_relevant_sites(query)
        
        # # Use provided time_range if specified, otherwise use suggested_time_range
        # final_time_range = time_range or suggested_time_range
        # logger.debug(f"Using time range: {final_time_range}")
        
        # Step 3: Enhance query with relevant sites
        enhanced_query = f"{optimized_query}"
        logger.debug(f"Enhanced query with relevant sites: {enhanced_query}")
        
        # Step 4: Execute the search with enhanced parameters
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            'q': enhanced_query,
            'num': limit * 2  # Request more results to filter down to higher quality ones
            
        })
        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        logger.debug(f"Search API call Response: {response.text}")
        results = response.json().get('organic', [])
        
        # Step 5: Filter and score results based on quality indicators
        scored_results = []
        
        # Extract key terms from the query for relevance scoring
        query_terms = set(re.findall(r'\w+', query.lower()))
        optimized_terms = set(re.findall(r'\w+', optimized_query.lower()))
        key_terms = query_terms.union(optimized_terms)
        
        for result in results:
            # Skip if no link
            if 'link' not in result or not result['link']:
                continue
                
            # Skip PDF files unless explicitly requested in the query
            if result['link'].endswith('.pdf') and 'pdf' not in query.lower():
                continue
                
            # Initialize score (lower is better)
            score = result.get('position', 999)
            
            # Analyze snippet for relevance if available
            snippet = result.get('snippet', '')
            title = result.get('title', '')
            
            # Increase score based on presence of key terms in snippet and title
            if snippet:
                snippet_terms = set(re.findall(r'\w+', snippet.lower()))
                # Calculate term overlap ratio
                overlap = len(key_terms.intersection(snippet_terms)) / len(key_terms) if key_terms else 0
                # Adjust score based on term overlap (higher overlap = lower score = better)
                score = score * (1 - (overlap * 0.5))
                
            # Boost score for results with key terms in title
            if title:
                title_terms = set(re.findall(r'\w+', title.lower()))
                title_overlap = len(key_terms.intersection(title_terms)) / len(key_terms) if key_terms else 0
                # Title matches are more important than snippet matches
                score = score * (1 - (title_overlap * 0.7))
            
            # Add to scored results
            scored_results.append({
                'link': result['link'],
                'score': score,
                'position': result.get('position', 999),
                'title': title,
                'snippet': snippet
            })
        
        # Sort results by score (lower is better)
        scored_results.sort(key=lambda x: x['score'])
        
        # Log detailed search results to file
        Search._save_search_log(query, enhanced_query, results=scored_results, search_type="smart")
        
        # Extract just the links from the top results up to the requested limit
        formatted_results = [result["link"] for result in scored_results[:limit]]
        
        # Check if we have any valid results
        if not formatted_results:
            logger.warning(f"No valid links found in smart search results.")
            # Fall back to regular search if smart search yields no results
            return Search.search(query, limit, time_range)
        
        logger.debug(f"Smart search formatted results: {formatted_results}")
        logger.debug("Smart search completed")
        return formatted_results

    @staticmethod
    def _determine_blend_ratio(query: str) -> dict:
        """
        Analyzes the query to determine the optimal blend ratio of different search types.
        
        Args:
            query: The search query to analyze
            
        Returns:
            Dictionary with recommended blend ratios for different search types
        """
        # Default ratio
        default_ratio = {'web': 0.7, 'news': 0.2, 'twitter': 0.1}
        
        # Convert query to lowercase for easier pattern matching
        query_lower = query.lower()
        
        # Check for news-related keywords
        news_keywords = ['news', 'recent', 'latest', 'update', 'breaking', 'today', 'yesterday', 
                         'week', 'month', 'announced', 'released', 'launched', 'published']
        news_score = sum(1 for keyword in news_keywords if keyword in query_lower)
        
        # Check for social media/Twitter-related keywords
        twitter_keywords = ['twitter', 'tweet', 'social media', 'opinion', 'reaction', 'trending',
                           'viral', 'hashtag', 'said on', 'commented', 'responded']
        twitter_score = sum(1 for keyword in twitter_keywords if keyword in query_lower)
        
        # Check for research/information keywords
        web_keywords = ['information', 'guide', 'tutorial', 'how to', 'learn', 'explain', 
                       'definition', 'meaning', 'history', 'background', 'research']
        web_score = sum(1 for keyword in web_keywords if keyword in query_lower)
        
        # Adjust ratios based on keyword scores
        if news_score > twitter_score and news_score > web_score:
            # News-heavy query
            return {'web': 0.3, 'news': 0.6, 'twitter': 0.1}
        elif twitter_score > news_score and twitter_score > web_score:
            # Twitter-heavy query
            return {'web': 0.3, 'news': 0.2, 'twitter': 0.5}
        elif news_score > 0 and twitter_score > 0:
            # Balanced query with news and social components
            return {'web': 0.4, 'news': 0.3, 'twitter': 0.3}
        elif news_score > 0:
            # Query with some news relevance
            return {'web': 0.5, 'news': 0.4, 'twitter': 0.1}
        elif twitter_score > 0:
            # Query with some social media relevance
            return {'web': 0.5, 'news': 0.1, 'twitter': 0.4}
        else:
            # Default to web-heavy for general information queries
            return default_ratio

    @staticmethod
    def blended_search(query: str, entities: dict, limit: int = 10, time_range: str = "24h", blend_ratio: dict = None) -> list:
        """
        Performs a blended search across multiple search types for more comprehensive results.
        
        Args:
            query: Search query
            limit: Maximum number of results
            time_range: Time range for search
            blend_ratio: Dictionary specifying the ratio of results to include from each search type.
                         Format: {'web': 0.6, 'news': 0.3, 'twitter': 0.1}
                         If None, will automatically determine based on query analysis.
            
        Returns:
            Blended list of search results optimized for accuracy and comprehensiveness
        """
        logger.debug(f"Starting blended search for '{query}' with limit {limit}")
        # Enhance search query with key entities
        entity1 = entities.get("entity1", "")
        entity2 = entities.get("entity2", "")
        entity3 = entities.get("entity3", "")
        enhanced_query = f"{query} {entity1} {entity2}"

        # Step 1: Analyze query to determine optimal blend ratio if not provided or invalid
        required_keys = {'web', 'news', 'twitter'}
        if blend_ratio is None or not isinstance(blend_ratio, dict) or not all(k in blend_ratio for k in required_keys):
            # If blend_ratio is None, empty, or missing required keys, determine it automatically
            blend_ratio = Search._determine_blend_ratio(query)
            
        logger.debug(f"Using blend ratio: {blend_ratio}")
        
        # Step 2: Calculate how many results to get from each source
        total_ratio = sum(blend_ratio.values())
        source_limits = {}
        for source, ratio in blend_ratio.items():
            # Calculate proportional limit and ensure at least 1 result if ratio > 0
            source_limits[source] = max(1, int(round((ratio / total_ratio) * limit))) if ratio > 0 else 0
            
        # Adjust limits to ensure we don't exceed the total requested limit
        while sum(source_limits.values()) > limit:
            # Find the source with the highest limit and reduce it by 1
            max_source = max(source_limits, key=source_limits.get)
            source_limits[max_source] -= 1
            
        logger.debug(f"Source limits: {source_limits}")
        
        # Step 3: Gather results from each source
        all_results = []
        
        # Web search
        if source_limits.get('web', 0) > 0:
            web_results = Search.smart_search(enhanced_query, source_limits['web'], time_range)
            all_results.extend([{'link': link, 'source': 'web'} for link in web_results])
            
        # News search
        if source_limits.get('news', 0) > 0:
            news_results = Search.search_news(enhanced_query, source_limits['news'], time_range)
            all_results.extend([{'link': link, 'source': 'news'} for link in news_results])
            
        # Twitter search
        if source_limits.get('twitter', 0) > 0:
            twitter_results = Search.search_twitter(enhanced_query, source_limits['twitter'], time_range)
            all_results.extend([{'link': link, 'source': 'twitter'} for link in twitter_results])
            
        # Step 4: Remove duplicates while preserving order
        seen_links = set()
        unique_results = []
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
                
        # Log blended search results to file
        Search._save_search_log(query, blend_ratio=blend_ratio, results=unique_results, search_type="blended")
                
        # Step 5: Return just the links, limited to the requested number
        formatted_results = [result['link'] for result in unique_results[:limit]]
        
        logger.debug(f"Blended search returned {len(formatted_results)} unique results")
        return formatted_results

def main():
    """Main execution function."""
    Search.search(query="Ilan Twig", limit=5, time_range="d")
    exit()

if __name__ == "__main__":
    main()