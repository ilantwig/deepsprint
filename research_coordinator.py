from datetime import date, datetime

from utils.config import default_model
from utils.capabilities.Search import Search
from utils.capabilities.Browser import Browser
import logging
import json
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def build_research_plan(research_topic: str) -> str:
    """
    Builds a research plan based on the given topic.
    
    Args:
        research_topic (str): The topic to create a research plan for
        
    Returns:
        str: A formatted research plan
    """
    # entity_type_prompt=f"Given the following topic: [{research_topic}], provide a brief, one-sentence description of what type of entity this is likely to be. Do not include any details beyond the entity type. For example, 'A technology startup' or 'A non-profit organization'."
    # entity_type_response=default_model.invoke(entity_type_prompt)
    # entity_type_response=entity_type_response.content.strip().replace("'","\"")
    # logger.debug(f"Response: {entity_type_response}")

    start_time = datetime.now()
    logger.debug(f"Starting research plan build at {start_time}")

    research_plan_prompt=f"""Example of a topic and the suggested research plan:
I want a detailed report on all Israeli hostages held by Hamas in Gaza:
(1) Find the exact number of Israeli hostages currently held by Hamas in Gaza.
(2) Find the names and ages of each hostage.
(3) Find the circumstances under which each hostage was captured.
(4) Find any information about the current conditions of the hostages and where they are being held.
(5) Find any statements or demands made by Hamas regarding the hostages.
(6) Find any statements or actions taken by the Israeli government regarding the hostages.
(7) Find any news articles or reports from reputable sources that provide updates on the situation.

Example of a topic and a suggested research plan:
Create a detailed profile on the startup mindtrip.ai by:
(1) Find the website of mindtrip.ai.
(2) Find news articles about mindtrip.ai.
(3) Find the funding history of mindtrip.ai.
(4) Find the profiles of the founders of mindtrip.ai.
(5) Find information about the products or services offered by mindtrip.ai.
(6) Find reviews or testimonials about mindtrip.ai.
(7) Find information about the target market and competitors of mindtrip.ai.
(8) Find any awards or recognition received by mindtrip.ai.

Example of a topic and a suggested research plan:
Create a detailed profile on Ilan Twig by:
(1) Find information on Ilan Twig's current and past roles at various companies.
(2) Find information on Ilan Twig's educational background.
(3) Find any interviews or articles where Ilan Twig has been quoted or featured.
(4) Find information on any awards or recognitions Ilan Twig has received.
(5) Find information on Ilan Twig's philanthropic activities or involvement in any non-profit organizations.
(6) Find information on Ilan Twig's social media presence and any insights it provides.

Based on that, create a research plan for: {research_topic}.  All steps are single line. All steps must include the context to the main research topic. Your response must be in JSON format. {{'step1':'<step description>'}}. Your response must start with {{"""
    logger.debug(f"Prompt: {research_plan_prompt}")
    research_plan_response=default_model.invoke(research_plan_prompt)
    research_plan_response=research_plan_response.content.strip()
    research_plan_response=research_plan_response.replace("```json","").replace("```","")
    logger.debug(f"Response: {research_plan_response}")

    research_plan_json = json.loads(research_plan_response)
    
    logger.debug(f"Research plan json: {research_plan_json}")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.debug(f"Research plan build completed in {duration}")
    return research_plan_json 

def deep_sprint_topic(step: str, previous_result: str) -> str:
    """
    Executes a specific research step.
    
    Args:
        step (str): The step to execute
        previous_result (str): Results from previous steps
        
    Returns:
        str: The result of the research step
    """




    start_time = datetime.now()
    logger.debug(f"Starting step execution at {start_time}")

    logger.debug(f"Executing step: {step}")

    search = Search()
    
    # Search with automatically determined relevant sites
    sites = search.search(step)
    
    # Initialize results string
    all_results = ""
    final_results = ""
    # Process each site
    for site in sites:
        try:
            # Use Browser's static method to scrape and summarize
            summary = Browser.scrape_and_summarize_web_page(site)
            
            # Add to results with source attribution
            all_results += f"\nSource: {site}\n{summary}\n"

        except Exception as e:
            logger.error(f"Error processing {site}: {str(e)}")
            continue
    topic_summary_prompot=f"""You are a research assistant. You are given a topic and content from multiple websites. Your goal is to sythesize the information into a comprehensive report on the topic.  Your response must be verbose and detailed.  Do not repeat the same information found in the previous results: {previous_result}.
    Topic: {step}
    Summary: {all_results}="""
    topic_summary_response=default_model.invoke(topic_summary_prompot)
    topic_summary_response=topic_summary_response.content.strip()
    logger.debug(f"Topic summary response: {topic_summary_response}")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.debug(f"Step execution completed in {duration}")
    return {
        'summary': topic_summary_response,
        'execution_time': str(duration)
    }

    

