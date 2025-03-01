from datetime import date, datetime
import re

from utils.config import default_model
from utils.utils import get_report_css_style
from utils.capabilities.Search import Search
from utils.capabilities.Browser import Browser
import logging
import json
from utils.crewid import CrewID
from config import test_mode
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def build_research_plan(research_topic: str) -> dict:
    """
    Builds a research plan based on the given topic.
    
    Args:
        research_topic (str): The topic to create a research plan for
        
    Returns:
        dict: A formatted research plan
    """
    start_time = datetime.now()
    logger.debug(f"Starting research plan build at {start_time}")

    # First, identify key entities in the research topic
    entity_prompt = f"""Given the following research topic: [{research_topic}], identify the 3 most important entities (people, companies, organizations, products, etc.) that are central to this topic.  Entiry can be a single word only!
    Your response must be in JSON format: {{"entity1":"<first key entity>", "entity2":"<second key entity>"}}. Your response must start with {{"""
    
    entity_response = default_model.invoke(entity_prompt)
    entity_response = entity_response.content.strip()
    entity_response = entity_response.replace("```json", "").replace("```", "")
    logger.debug(f"Entity Response: {entity_response}")
    
    entities_json = json.loads(entity_response)
    logger.debug(f"Entities json: {entities_json}")

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
Create a detailed profile on the startup mindcool.ai by:
(1) Find general information about mindcool.ai.
(2) Find news articles about mindcool.ai.
(3) Find the funding history of mindcool.ai.
(4) Find the profiles of the founders of mindcool.ai.
(5) Find information about the products or services offered by mindcool.ai.
(6) Find reviews or testimonials about mindcool.ai.
(7) Find information about the target market and competitors of mindcool.ai.
(8) Find any awards or recognition received by mindcool.ai.

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
    
    # Generate search terms for each step
    search_terms = {}
    for step_key, step_value in research_plan_json.items():
        if step_key.startswith("step"):
            search_term_prompt = f"generate a google search term to address this: {step_value}.  Respond in json format: {{'search_term':'<search term>'}}.  Youre response must start with {{"
            search_term_response = default_model.invoke(search_term_prompt)
            search_term = search_term_response.content.strip()
            search_terms[step_key] = search_term
            logger.debug(f"Generated search term for {step_key}: {search_term}")
    
    # Add search terms to the research plan JSON
    research_plan_json["search_terms"] = search_terms
    
    # Add entities and research topic to the research plan JSON
    research_plan_json["entities"] = entities_json
    research_plan_json["research_topic"] = research_topic
    
    # Save the research plan to a file
    from utils.capabilities.File import File
    crewid = CrewID.get_crewid()
    
    # # Save the research topic
    # File.write_file(crewid, "research", "research_topic.txt", research_topic)
    
    # Save the research plan with entities
    File.write_file(crewid, "", "research_plan.json", json.dumps(research_plan_json))
    
    # # Save entities for later use in deep_sprint_topic
    # File.write_file(crewid, "research", "entities.json", json.dumps(entities_json))
    
    logger.debug(f"Research plan: {research_plan_json}")
    logger.debug(f"Entities: {entities_json}")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.debug(f"Research plan build completed in {duration}")
    
    # Return only the plan part, not the entire result object
    return research_plan_json

def deep_sprint_topic(step: str, step_number: int, entities: dict, search_term: str = None) -> str:
    """
    Executes a specific research step.
    
    Args:
        step (str): The step to execute
        step_number (int): The number of the current step
        entities (dict): Key entities identified for the research topic
        search_term (str, optional): The search term to use instead of the step description
        
    Returns:
        str: The result of the research step
    """

    start_time = datetime.now()
    logger.debug(f"Starting step execution at {start_time}")

    logger.debug(f"Executing step: {step}")
    
    # If a search term is provided, use it; otherwise, use the step description
    if search_term:
        # Parse the search term from JSON if it's a JSON string
        try:
            search_term_json = json.loads(search_term)
            if isinstance(search_term_json, dict) and 'search_term' in search_term_json:
                query = search_term_json['search_term']
            else:
                query = search_term
        except (json.JSONDecodeError, TypeError):
            # If it's not valid JSON or is None, use it as is
            query = search_term
    else:
        query = step
    
    # Enhance search query with key entities
    entity1 = entities.get("entity1", "")
    entity2 = entities.get("entity2", "")
    entity3 = entities.get("entity3", "")
    enhanced_query = f"{query} {entity1} {entity2} {entity3}".strip()
    logger.debug(f"Enhanced search query: {enhanced_query}")

    search = Search()
    
    # Search with automatically determined relevant sites and enhanced query
    sites = search.search(enhanced_query)
    
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
    # For testing, you can set this environment variable to use mock data
    if test_mode:
        topic_summary_response = """<style>
        body {
            font-family: Arial;
        }
        </style>
        <h1>Mock Research Report</h1>
        <p>This is a mock research report for step: {step}</p>
        <h2>Key Findings</h2>
        <ul>
            <li>Finding 1: Lorem ipsum dolor sit amet</li>
            <li>Finding 2: Consectetur adipiscing elit</li>
            <li>Finding 3: Sed do eiusmod tempor</li>
        </ul>
        <h2>Detailed Analysis</h2>
        <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
        <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
        """.format(step=step)
    else:
        today = date.today()
        topic_summary_prompot=f"""Date: {today}.
You are a research assistant. You are given a topic and content from multiple websites. Your goal is to sythesize the information into a comprehensive html report on the topic. DO NOT HAVE A CONCLUSION section. Your response must be verbose and detailed.
Topic: {step}
Key Entities: {entity1}, {entity2}
Summary: {all_results}="""
        topic_summary_response=default_model.invoke(topic_summary_prompot)
        topic_summary_response=topic_summary_response.content.strip()
        topic_summary_response=topic_summary_response.replace("```html","").replace("```","")
    
    # Define the CSS style
    css_style = get_report_css_style()

    # Remove any existing style tags
    topic_summary_response = re.sub(r'<style>.*?</style>', '', topic_summary_response, flags=re.DOTALL)
    
    # Add our custom style at the beginning of the HTML content
    topic_summary_response = css_style + topic_summary_response

    # Save individual step report
    from utils.capabilities.File import File
    crewid = CrewID.get_crewid()
    output_path = f"step_report.html"
    File.write_file(crewid, step_number, output_path, topic_summary_response)

    end_time = datetime.now()
    duration = end_time - start_time
    logger.debug(f"Step execution completed in {duration}")
    return {
        'summary': topic_summary_response,
        'execution_time': str(duration)
    }
def generate_final_report(all_results: str) -> str:
    """
    Generates a final report from all the results.
    
    Args:
        all_results (str): All the results from the research steps  
    
    Returns:
        str: The final report
    """
    today = date.today()
    final_report_prompt=f"""Date: {today}.
Create a verbose, detailed executive summary report in html from below content.  You must include MOST of the details from the original content. Feel free to restructure it, use tables, lists, etc.  Have a conclusion section with cross data insights.
Content: {all_results}="""

    final_report_response=default_model.invoke(final_report_prompt)
    final_report_response=final_report_response.content.strip()
    final_report_response=final_report_response.replace("```html","").replace("```","")
    logger.debug(f"Final report response: {final_report_response}")

    # Define the CSS style
    css_style = get_report_css_style()

    # Remove any existing style tags
    final_report_response = re.sub(r'<style>.*?</style>', '', final_report_response, flags=re.DOTALL)
    
    # Add our custom style at the beginning of the HTML content
    final_report_response = css_style + final_report_response

    # Save final report
    from utils.capabilities.File import File
    crewid = CrewID.get_crewid()
    output_path = f"final_report.html"
    File.write_file(crewid, "final", output_path, final_report_response)

    return final_report_response

