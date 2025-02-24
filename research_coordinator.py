from datetime import date, datetime

from utils.config import default_model
from utils.capabilities.Search import Search
from utils.capabilities.Browser import Browser
import logging
import json
from utils.crewid import CrewID
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
(1) Find general information about mindtrip.ai.
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

def deep_sprint_topic(step: str, step_number: int) -> str:
    """
    Executes a specific research step.
    
    Args:
        step (str): The step to execute
        step_number (int): The number of the current step
        
    Returns:
        str: The result of the research step
    """
#     return {
#         'summary': """Find information on any awards or recognitions Ilan Twig has received.
# **Comprehensive Report on Awards and Recognitions Received by Ilan Twig** Ilan Twig is a prominent figure in the tech industry, particularly known for his role as the co-founder and Chief Technology Officer (CTO) of Navan, Inc., formerly known as TripActions. His career is marked by significant achievements and contributions to corporate travel management. While the sources provided extensively cover the growth and success of TripActions/Navan, details on specific awards or recognitions directly attributed to Ilan Twig are scarce. However, the following synthesis highlights relevant aspects of his professional journey and associated accolades through the achievements of TripActions/Navan, which indirectly reflect on his contributions and leadership. ### Professional Background and Contributions Ilan Twig, based in Mountain View, California, has established a robust professional presence, particularly in the areas of cloud computing and AI-driven solutions for business travel. He has been instrumental in the success and expansion of Navan, a company co-founded with Ariel Cohen. Navan has evolved into a leader in corporate travel management, integrating AI to enhance the traveler experience and streamline expense management. ### Indirect Recognitions through TripActions/Navan 1. **Company Growth and Valuation:** - Under the leadership of Ilan Twig and Ariel Cohen, TripActions (now Navan) has experienced rapid growth, securing significant funding rounds. Notably, the company achieved a valuation exceeding $1 billion, earning a place in the 'Global Unicorn Club.' This milestone reflects the effective leadership and innovative solutions developed under Twig's technical guidance. 2. **Funding and Recognition from Prestigious Investors:** - The company has received substantial investments from leading venture capital firms such as Andreessen Horowitz and Lightspeed Venture Partners. The involvement of such reputable investors underscores the company's strong market position and the confidence in its leadership team, including Twig. 3. **Cultural and Leadership Accolades:** - TripActions has been recognized for its company culture and leadership, receiving employee-voted awards from Comparably. These acknowledgments include rankings for Best Company Culture and Best CEO, highlighting the positive work environment and visionary leadership fostered by the company's founders. 4. **Innovative Product Development:** - The launch of TripActions Liquid, an integrated payment and expense management platform, exemplifies the innovative spirit and technical prowess brought forth by Twig. This product development has further solidified the company's reputation as a leader in corporate travel solutions. ### Patents and Publications Ilan Twig holds several patents related to web navigation and data integration, showcasing his innovative contributions to technology. His work has been published, further emphasizing his expertise and thought leadership in the tech industry. ### Recommendations and Professional Endorsements Twig has received numerous professional recommendations praising his engineering skills, leadership, and impact on technology and team management. These endorsements from peers and industry professionals highlight his influence and effectiveness in his field. ### Conclusion While specific awards or recognitions directly attributed to Ilan Twig were not explicitly detailed in the sources, his leadership and technical innovations have significantly contributed to the success and recognition of Navan. The achievements of the company, including its rapid growth, industry accolades, and esteemed investor backing, indirectly reflect the high regard for Twig's contributions and expertise in his domain.
# """,
#         'execution_time': str(2)
#     }



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
    topic_summary_prompot=f"""You are a research assistant. You are given a topic and content from multiple websites. Your goal is to sythesize the information into a comprehensive html report on the topic. DO NOT HAVE A CONCLUSION section. Your response must be verbose and detailed.
    Topic: {step}
    Summary: {all_results}="""
    topic_summary_response=default_model.invoke(topic_summary_prompot)
    topic_summary_response=topic_summary_response.content.strip()
    topic_summary_response=topic_summary_response.replace("```html","").replace("```","")
    logger.debug(f"Topic summary response: {topic_summary_response}")

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
    final_report_prompt=f"""Create a verbose, detailed executive summary report in html from below content.  You must include MOST of the details from the original content. Feel free to restructure it, use tables, lists, etc.  Have a conclusion section with cross data insights.
    Content: {all_results}="""
    final_report_response=default_model.invoke(final_report_prompt)
    final_report_response=final_report_response.content.strip()
    final_report_response=final_report_response.replace("```html","").replace("```","")
    logger.debug(f"Final report response: {final_report_response}")

    # Save final report
    from utils.capabilities.File import File
    crewid = CrewID.get_crewid()
    output_path = f"final_report.html"
    File.write_file(crewid, "final", output_path, final_report_response)
    return final_report_response

