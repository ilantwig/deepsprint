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
from utils.capabilities.File import File
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

logging.getLogger("_base_client").disabled = True


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
    entity_prompt = f"""Given the following research topic: [{research_topic}], identify the 3 most important entities (people, companies, organizations, products, etc.) that are central to this topic.  Entity can be a single word only!
    
Your response must be in JSON format with exactly three entities:
{{
    "entity1": "<first key entity>",
    "entity2": "<second key entity>",
    "entity3": "<third key entity>"
}}

Your response must start with {{ and must be valid JSON. Do not include any explanatory text outside the JSON structure."""
    
    # Save the entity prompt
    crewid = CrewID.get_crewid()
    File.save_prompt(crewid, "entity_identification", entity_prompt)
    
    entity_response = default_model.invoke(entity_prompt)
    entity_response = entity_response.content.strip()
    entity_response = entity_response.replace("```json", "").replace("```", "")
    logger.debug(f"Entity Response: {entity_response}")
    
    try:
        entities_json = json.loads(entity_response)
        logger.debug(f"Entities json: {entities_json}")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing entities JSON: {e}")
        logger.error(f"Raw response: {entity_response}")
        
        # Attempt to extract JSON from the response if it contains JSON-like content
        import re
        json_pattern = r'({.*})'
        match = re.search(json_pattern, entity_response, re.DOTALL)
        
        if match:
            try:
                potential_json = match.group(1)
                logger.debug(f"Attempting to parse extracted JSON: {potential_json}")
                entities_json = json.loads(potential_json)
                logger.debug(f"Successfully extracted and parsed JSON from response: {entities_json}")
            except json.JSONDecodeError:
                # If extraction fails, create a basic fallback entities
                logger.error("Failed to extract valid JSON, using fallback entities")
                entities_json = {
                    "entity1": research_topic.split()[0] if research_topic.split() else "Topic",
                    "entity2": research_topic.split()[1] if len(research_topic.split()) > 1 else "Research",
                    "entity3": research_topic.split()[2] if len(research_topic.split()) > 2 else "Information"
                }
        else:
            # If no JSON-like content is found, use the fallback entities
            logger.error("No JSON-like content found in response, using fallback entities")
            entities_json = {
                "entity1": research_topic.split()[0] if research_topic.split() else "Topic",
                "entity2": research_topic.split()[1] if len(research_topic.split()) > 1 else "Research",
                "entity3": research_topic.split()[2] if len(research_topic.split()) > 2 else "Information"
            }

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

Example of a topic and a suggested research plan:
Which animals are better dolphins or sharks?
(1) Find articles and studies comparing dolphins and sharks as pets.
(2) Find information about the different breeds of dolphins and sharks.
(3) Find information about the different personalities of dolphins and sharks.
(4) Find information about the different health needs of dolphins and sharks.
(5) Find information about the different training needs of dolphins and sharks.
(6) Find information about the different costs of owning a dog or cat.

Based on that, create a research plan for: {research_topic}

Your response must be in JSON format with step keys and descriptions:
{{
    "step1": "First step description",
    "step2": "Second step description",
    ...
}}

Your response must start with {{ and must be valid JSON. Do not include any explanatory text outside the JSON structure."""

    # Save the research plan prompt
    File.save_prompt(crewid, "research_plan_generation", research_plan_prompt)
    
    logger.debug(f"Prompt: {research_plan_prompt}")
    research_plan_response=default_model.invoke(research_plan_prompt)
    research_plan_response=research_plan_response.content.strip()
    research_plan_response=research_plan_response.replace("```json","").replace("```","")
    logger.debug(f"Response: {research_plan_response}")

    try:
        research_plan_json = json.loads(research_plan_response)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing research plan JSON: {e}")
        logger.error(f"Raw response: {research_plan_response}")
        
        # Attempt to extract JSON from the response if it contains JSON-like content
        import re
        json_pattern = r'({.*})'
        match = re.search(json_pattern, research_plan_response, re.DOTALL)
        
        if match:
            try:
                potential_json = match.group(1)
                logger.debug(f"Attempting to parse extracted JSON: {potential_json}")
                research_plan_json = json.loads(potential_json)
                logger.debug("Successfully extracted and parsed JSON from response")
            except json.JSONDecodeError:
                # If extraction fails, create a basic fallback plan
                logger.error("Failed to extract valid JSON, using fallback plan")
                research_plan_json = {
                    "step1": "Research general information about the topic",
                    "step2": "Find specific details related to the main aspects",
                    "step3": "Explore practical applications or implications",
                    "step4": "Analyze different perspectives or approaches",
                    "step5": "Compile recommendations or conclusions"
                }
        else:
            # If no JSON-like content is found, use the fallback plan
            logger.error("No JSON-like content found in response, using fallback plan")
            research_plan_json = {
                "step1": "Research general information about the topic",
                "step2": "Find specific details related to the main aspects",
                "step3": "Explore practical applications or implications",
                "step4": "Analyze different perspectives or approaches",
                "step5": "Compile recommendations or conclusions"
            }
    
    # Generate search terms for each step in a single LLM call
    search_terms = {}
    steps_for_search = {}
    for step_key, step_value in research_plan_json.items():
        if step_key.startswith("step"):
            steps_for_search[step_key] = step_value
    
    if steps_for_search:
        search_term_prompt = f"""For each of the following research steps, generate an appropriate Google search term.
        
{json.dumps(steps_for_search, indent=2)}
        
Respond in JSON format with the step keys and their corresponding search terms:
{{
    "step1": "example search term for step 1",
    "step2": "example search term for step 2",
    ...
}}

Your response must start with {{ and must be valid JSON. Do not include any explanatory text outside the JSON structure."""
        
        # Save the search term prompt
        File.save_prompt(crewid, "search_term_generation", search_term_prompt)
        
        search_term_response = default_model.invoke(search_term_prompt)
        search_terms_json = search_term_response.content.strip()
        search_terms_json = search_terms_json.replace("```json", "").replace("```", "")
        logger.debug(f"Generated search terms: {search_terms_json}")
        
        try:
            search_terms = json.loads(search_terms_json)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing search terms JSON: {e}")
            logger.error(f"Raw response: {search_terms_json}")
            
            # Attempt to extract JSON from the response if it contains JSON-like content
            import re
            json_pattern = r'({.*})'
            match = re.search(json_pattern, search_terms_json, re.DOTALL)
            
            if match:
                try:
                    potential_json = match.group(1)
                    logger.debug(f"Attempting to parse extracted JSON: {potential_json}")
                    search_terms = json.loads(potential_json)
                    logger.debug("Successfully extracted and parsed JSON from response")
                except json.JSONDecodeError:
                    # If extraction fails, create empty dict
                    logger.error("Failed to extract valid JSON, using empty dict")
                    search_terms = {}
            else:
                # If no JSON-like content is found, use empty dict
                logger.error("No JSON-like content found in response, using empty dict")
                search_terms = {}
    
    # Add search terms to the research plan JSON
    research_plan_json["search_terms"] = search_terms
    
    # Add entities and research topic to the research plan JSON
    research_plan_json["entities"] = entities_json
    research_plan_json["research_topic"] = research_topic
    
    # Save the research plan to a file
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
    Executes a deep sprint on a specific topic.
    
    Args:
        step (str): The research step to execute
        step_number (int): The step number
        entities (dict): The entities to use for the search
        search_term (str, optional): The search term to use. Defaults to None.
        
    Returns:
        str: The result of the deep sprint
    """
    start_time = datetime.now()
    logger.debug(f"Starting deep sprint for step {step_number} at {start_time}")
    
    # Extract entities
    entity1 = entities.get("entity1", "")
    entity2 = entities.get("entity2", "")
    entity3 = entities.get("entity3", "")
    
    # Use the provided search term if available, otherwise use the step as the search term
    if not search_term:
        search_term = step
    
    logger.debug(f"Using search term: {search_term}")
    
    # Optimize the search query
    optimized_query = Search.optimize_query(search_term)
    logger.debug(f"Optimized query: {optimized_query}")
    
    # Perform the search
    search_results = Search.search(optimized_query, 40)
    
    # Extract URLs from search results
    urls = []
    for result in search_results:
        if isinstance(result, dict) and 'link' in result:
            urls.append(result['link'])
        elif isinstance(result, str):
            urls.append(result)
    
    logger.debug(f"Found {len(urls)} URLs")
    
    # Browse the URLs and extract content
    all_results = ""
    results_limit = 10
    for i, url in enumerate(urls[:results_limit]):  # Limit to first 3 URLs for now
        try:
            logger.debug(f"Browsing URL {i+1}/{len(urls[:results_limit])}: {url}")
            content = Browser.scrape_and_summarize_web_page(url)
            if content and not ("Error scraping" in content):
                all_results += f"\n\nSource {i+1} ({url}):\n{content}\n"
            else:
                logger.error(f"Error scraping URL {url}: {content}")
        except Exception as e:
            logger.error(f"Error browsing URL {url}: {e}")
    
    if test_mode:
        topic_summary_response = f"""
        <h1>Research Findings for Step {step_number + 1}</h1>
        <p>This is a mock response for testing purposes.</p>
        <h2>Key Insights</h2>
        <ul>
            <li>Finding 1: Lorem ipsum dolor sit amet</li>
            <li>Finding 2: Consectetur adipiscing elit</li>
            <li>Finding 3: Sed do eiusmod tempor incididunt</li>
        </ul>
        <p>Source: <a href="https://example.com">Example.com</a></p>
        """
    else:
        today = date.today()
        topic_summary_prompt=f"""Date: {today}.
You are a research assistant. You are given a topic and content from multiple websites. Your goal is to sythesize the information into a comprehensive html report on the topic. Key findings, common points.  Convert findings into tables, charts or structured bullet points. DO NOT HAVE A CONCLUSION section. Your response must be verbose and detailed. Have a citation section in the bottom.
Topic: {step}
Key Entities: {entity1}, {entity2}, {entity3}
Summary: {all_results}="""

        # Save the topic summary prompt
        crewid = CrewID.get_crewid()
        File.save_prompt(crewid, f"step_{step_number}_summary", topic_summary_prompt)
        
        topic_summary_response=default_model.invoke(topic_summary_prompt)
        topic_summary_response=topic_summary_response.content.strip()
        topic_summary_response=topic_summary_response.replace("```html","").replace("```","")
    
    # Define the CSS style
    css_style = get_report_css_style()

    # Remove any existing style tags
    topic_summary_response = re.sub(r'<style>.*?</style>', '', topic_summary_response, flags=re.DOTALL)
    
    # Add our custom style at the beginning of the HTML content
    topic_summary_response = css_style + topic_summary_response

    # Save individual step report
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
    
    # Get the research topic from the research plan file
    crewid = CrewID.get_crewid()
    research_topic = ""
    
    try:
        research_plan_content = File.read_file(crewid, "", "research_plan.json")
        if research_plan_content:
            research_plan = json.loads(research_plan_content)
            research_topic = research_plan.get("research_topic", "")
    except Exception as e:
        logger.error(f"Error retrieving research topic: {e}")
        research_topic = "Research Topic"  # Fallback if we can't get the actual topic
    
#     final_report_prompt=f"""Date: {today}.
# Create a verbose, detailed executive summary in html from below content. Make sure to specifically address the topic: {research_topic}. Summarize key findings. You must include MOST of the details from the original content. Convert findings into charts, tables or structured bullet points  Add insights that can only be derived from looking at all of the content.  Present the information in a way that is easy to understand and use. Keep all citations.  Again, make sure to specifically address the topic: {research_topic}.
# Content: {all_results}="""
    
    final_report_prompt=f"""Date: {today}.
Generate a comprehensive executive summary addressing: "{research_topic}"

Using the provided sub-topic reports, create a clear and organized HTML report that:
1. Directly answers the main question/addresses the topic
2. Synthesizes key findings from all sub-topic reports
3. Highlights important patterns and connections
4. Presents conclusions and implications

Format the report with:
- An executive summary (2-3 paragraphs)
- Key findings in bullet points
- Supporting data in tables where relevant
- Clear section headings
- Final conclusion that explicitly addresses the original query

Data
{all_results}"""

    # Save the final report prompt
    File.save_prompt(crewid, "final_report", final_report_prompt)
    
    final_report_response = default_model.invoke(final_report_prompt)
    final_report = final_report_response.content.strip()
    
    # Clean up the response
    final_report = final_report.replace("```html", "").replace("```", "")
    
    # Add CSS style
    css_style = get_report_css_style()
    final_report = re.sub(r'<style>.*?</style>', '', final_report, flags=re.DOTALL)
    final_report = css_style + final_report
    
    # Save the final report
    File.write_file(crewid, "final", "final_report.html", final_report)
    
    return final_report

