import warnings
import logging
import sys
# Filter out Pydantic's deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", ".*Pydantic V1.*")
warnings.filterwarnings("ignore", ".*PydanticDeprecatedSince20.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="flask_session")

# Suppress Flask's internal logging
logging.getLogger("werkzeug").disabled = True
# Suppress _internal.py logging
logging.getLogger("werkzeug._internal").disabled = True
# Suppress _config.py and _trace.py logging
logging.getLogger("_config").disabled = True
logging.getLogger("_trace").disabled = True

# More aggressive approach to suppress specific modules
for logger_name in ["werkzeug", "_internal", "_config", "_trace", "httpx", "httpcore", "urllib3", "LiteLLM"]:
    logger = logging.getLogger(logger_name)
    logger.disabled = True
    logger.setLevel(logging.ERROR)  # Set to ERROR level as fallback if disabling doesn't work

# Add a filter to the root logger to block specific module logs
class ModuleFilter(logging.Filter):
    def __init__(self, blocked_modules):
        super().__init__()
        self.blocked_modules = blocked_modules
        
    def filter(self, record):
        # Return False to block the log message
        return not any(module in record.pathname for module in self.blocked_modules)

# Apply the filter to the root logger
root_logger = logging.getLogger()
root_logger.addFilter(ModuleFilter(['_internal.py', '_config.py', '_trace.py']))

# Configure logging only once
if not getattr(sys, 'logging_configured', False):
    # Set the logging level for all loggers to ERROR
    logging.basicConfig(level=logging.ERROR)
    
    # Mark logging as configured
    sys.logging_configured = True

# Now import the rest of the modules
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, make_response
from flask_cors import CORS
from pathlib import Path
from research_coordinator import build_research_plan, deep_sprint_topic, generate_final_report
import json
from threading import Thread
from queue import Queue
from argparse import ArgumentParser
from config import test_mode, set_test_mode
from os import getenv
from dotenv import load_dotenv, set_key
import os  # Add this import for os.environ
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from utils.crewid import CrewID
from xhtml2pdf import pisa
from io import BytesIO
import tempfile
from datetime import datetime


logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logging.getLogger("_base_client").disabled = True

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000"], "supports_credentials": True}})

load_dotenv()

# Add this near the top of your file, with other global variables
research_plan_cache = {}

# Add these configurations after creating the Flask app but before Session(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)  # or a fixed secret key
csrf = CSRFProtect(app)
Session(app)

def get_model_status():
    openai_model = getenv('OPENAI_MODEL_NAME')
    openai_key = getenv('OPENAI_API_KEY')
    lm_studio_url = getenv('LM_STUDIO_URL')
    
    if openai_model and openai_key and openai_key.startswith('sk-'):
        return f"Using {openai_model}"
    elif lm_studio_url:
        return "Using LM Studio"
    else:
        return "No model configured"

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/')
def index():
    model_status = get_model_status()  # Get the model status
    crewid = CrewID.get_crewid()  # Get the crew ID
    return render_template('index.html', test_mode=test_mode, model_status=model_status, crewid=crewid)

@app.route('/regenerate', methods=['POST'])
def regenerate_plan():
    research_topic = request.form['research_topic']
    
    # Force regeneration of a new 4-digit crewID
    CrewID.generate_crewid()
    
    research_plan = build_research_plan(research_topic)
    
    # Extract just the research steps, excluding entities and research_topic
    research_steps = {k: v for k, v in research_plan.items() 
                     if k.startswith('step') and not k in ['entities', 'research_topic', 'search_terms']}
    
    # Get the search terms
    search_terms = research_plan.get('search_terms', {})
    
    # Return only the steps in the response, but keep entities and search_terms separate
    return jsonify(research_plan=research_steps, 
                  research_results=None, 
                  test_mode=test_mode,
                  crewid=CrewID.get_crewid(),
                  entities=research_plan.get('entities', {}),
                  search_terms=search_terms)  # Include search_terms

@app.route('/execute_deep_sprint', methods=['POST'])
def execute_deep_sprint():
    research_steps = request.json.get('research_steps', [])
    entities = request.json.get('entities', {})
    research_id = CrewID.get_crewid()
    
    # Try to get search_terms and entities from cache first
    if research_id in research_plan_cache:
        search_terms = research_plan_cache[research_id].get('search_terms', {})
        # If entities were passed empty but we have them in cache, use the cached ones
        if not entities and 'entities' in research_plan_cache[research_id]:
            entities = research_plan_cache[research_id].get('entities', {})
        logger.debug(f"Search terms and entities loaded from cache for research_id: {research_id}")
    else:
        # Load from file if not in cache
        research_plan_path = f"output/{research_id}/_research_plan.json"
        try:
            with open(research_plan_path, 'r') as f:
                research_plan = json.load(f)
                # Store in cache for future use
                research_plan_cache[research_id] = research_plan
                search_terms = research_plan.get('search_terms', {})
                # If entities were passed empty but exist in the file, use those
                if not entities and 'entities' in research_plan:
                    entities = research_plan.get('entities', {})
                logger.debug(f"Search terms and entities loaded from file and cached for research_id: {research_id}")
        except Exception as e:
            logger.error(f"Error loading search terms from research plan: {e}")
            search_terms = {}
    
    # Add debug logging
    logger.debug(f"Search terms: {search_terms}")
    logger.debug(f"Entities: {entities}")
    logger.debug(f"Research steps: {research_steps}")
    
    # Convert research_steps to a dictionary if it's a list
    if isinstance(research_steps, list):
        research_steps_dict = {}
        for i, step in enumerate(research_steps):
            logger.debug(f"Step {i+1}: {step}")
            step_key = f"step{i+1}"
            research_steps_dict[step_key] = step
        research_steps = research_steps_dict

    result_queue = Queue()
    results_container = {'all_results': ''}

    def process_step(step, step_num, step_key):
        try:
            # Use the global test_mode variable instead of hardcoded value
            if test_mode:
                mock_text = f"""
                Detailed research findings for step {step_num + 1}: {step}
                
                Analysis:
                The investigation into this aspect revealed several key insights. First, we identified multiple perspectives on the topic including historical context and recent developments. The data suggests a correlation between several factors that influence the outcome significantly.
                
                Key findings:
                1. Primary discovery shows a strong relationship between variables
                2. Secondary elements indicate potential applications in related domains
                3. Unexpected patterns emerged during the third phase of analysis
                4. Literature review confirms the validity of these observations
                
                Implications:
                These findings suggest broader applications and raise new questions for further exploration. The methodology applied here could be extended to similar research domains.
                """
                result = {
                    'summary': mock_text.strip(),
                    'execution_time': '1.2s'
                }
            else:
                # Get the search term for this step if available
                search_term = None  # Initialize search_term with a default value
                if step_key in search_terms:
                    search_term = search_terms[step_key]
                    logger.debug(f"Using search term for {step_key}: {search_term}")
                else:
                    logger.debug(f"No search term found for {step_key}")
                
                logger.debug(f"Executing deep sprint for step {step_num+1} with search term: {search_term}")
                result = deep_sprint_topic(step, step_num, entities, search_term)
                logger.debug(f"Completed deep sprint for step {step_num+1}")
            
            result_dict = {
                'step': step_num + 1,
                'step_value': step,
                'result': result['summary'],
                'execution_time': result['execution_time']
            }
            result_queue.put(result_dict)
            # Append to string with formatting using the container
            results_container['all_results'] += f"\nStep {step_num + 1}:\n{result['summary']}\n"
        except Exception as e:
            error_dict = {
                'step': step_num + 1,
                'error': str(e)
            }
            result_queue.put(error_dict)
            # Append error to string using the container
            results_container['all_results'] += f"\nStep {step_num + 1} Error:\n{str(e)}\n"

    def generate():
        # Start all threads
        threads = []
        for i, (step_key, step_value) in enumerate(research_steps.items()):
            thread = Thread(target=process_step, args=(step_value, i, step_key))
            thread.start()
            threads.append(thread)

        # Yield results as they become available
        results_received = 0
        while results_received < len(research_steps):
            result = result_queue.get()
            results_received += 1
            yield f"{json.dumps(result)}\n"

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Use the container to access all_results
        if results_container['all_results']:
            if test_mode:
                final_report = """
                # Comprehensive Research Synthesis
                
                ## Executive Summary
                This report consolidates findings from multiple research steps exploring the designated topic. The investigation revealed interconnected themes and actionable insights across several dimensions of the subject matter.
                
                ## Methodology Overview
                The research implemented a multi-phase approach with parallel investigation streams. Each step focused on distinct aspects while maintaining coherence with the overall research question.
                
                ## Key Findings
                1. **Primary Observations**: Analysis identified recurring patterns across data sources, suggesting fundamental principles underlying the phenomenon.
                
                2. **Contextual Factors**: Environmental and situational variables significantly influence outcomes in ways previously underappreciated in the literature.
                
                3. **Emerging Trends**: Recent developments indicate a shift in paradigm that warrants further exploration and potentially new theoretical frameworks.
                
                4. **Limitations**: Current methodological approaches show specific constraints when applied to certain edge cases.
                
                ## Synthesis of Results
                The combined evidence points toward a coherent narrative that bridges previously disconnected concepts. The interrelationships between various factors demonstrate complex but discernible patterns.
                
                ## Recommendations
                Based on these findings, several avenues for further investigation appear promising:
                - Exploration of newly identified correlations
                - Development of targeted interventions based on discovered principles
                - Refinement of existing theoretical models to accommodate new insights
                
                ## Conclusion
                This research provides a foundation for deeper understanding and practical applications within the domain. The multi-faceted approach has yielded a more nuanced perspective than previous single-dimension studies.
                """
            else:
                final_report = generate_final_report(results_container['all_results'])
            yield f"{json.dumps({'final_report': final_report})}\n"

    return Response(
        stream_with_context(generate()),
        mimetype='application/x-ndjson'
    )

@app.route('/list_research', methods=['GET'])
def list_research():
    try:
        output_dir = Path('output')
        if not output_dir.exists():
            return jsonify({'folders': []})
            
        # Get all subdirectories (crew IDs)
        folders = [f.name for f in output_dir.iterdir() if f.is_dir()]
        return jsonify({'folders': folders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_research/<crewid>', methods=['GET'])
def get_research(crewid):
    try:
        crew_dir = Path(f'output/{crewid}')
        if not crew_dir.exists():
            return jsonify({'error': 'Research not found'}), 404
            
        # Get research plan
        plan_file = crew_dir / '_research_plan.json'  # Try with underscore prefix first
        if not plan_file.exists():
            plan_file = crew_dir / 'research_plan.json'  # Then try without underscore
            
        research_plan = {}
        entities = {}
        if plan_file.exists():
            try:
                with open(plan_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # Check if file is not empty
                        full_plan = json.loads(content)
                        # Extract entities separately
                        if 'entities' in full_plan:
                            entities = full_plan.pop('entities')
                        # Filter out non-step fields
                        research_plan = {k: v for k, v in full_plan.items() 
                                        if k.startswith('step') or k == 'research_topic'}
                    else:
                        logger.warning(f"Empty research plan file for crew {crewid}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding research plan for crew {crewid}: {e}")
                # Try to recover the file content as plain text
                try:
                    with open(plan_file, 'r') as f:
                        content = f.read().strip()
                    if content:
                        # Store as a single step if we can't parse JSON
                        research_plan = {"step1": content}
                except Exception:
                    pass
        
        # Get research topic - first try from research_topic.txt
        topic_file = crew_dir / 'research_topic.txt'
        research_topic = ""
        if topic_file.exists():
            try:
                with open(topic_file, 'r') as f:
                    research_topic = f.read().strip()
            except Exception as e:
                logger.error(f"Error reading research topic for crew {crewid}: {e}")
        
        # If no topic found, try to get it from research_plan.json
        if not research_topic and 'research_topic' in research_plan:
            research_topic = research_plan.pop('research_topic')  # Remove from plan after extracting
        
        # Get research results
        results_file = crew_dir / 'research_results.json'
        research_results = {}
        
        # First try the standard JSON file
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    content = f.read().strip()
                    if content:  # Check if file is not empty
                        # Try to parse as JSON first
                        try:
                            research_results = json.loads(content)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, it might be HTML content
                            # Store it as a single result
                            research_results = {"1": content}
                    else:
                        logger.warning(f"Empty research results file for crew {crewid}")
            except Exception as e:
                logger.error(f"Error reading research results file for crew {crewid}: {e}")
        
        # If no results found, check for individual HTML files (like 0_step_report.html)
        if not research_results:
            step_files = list(crew_dir.glob('*_step_report.html'))
            if step_files:
                logger.info(f"Found {len(step_files)} individual step report files for crew {crewid}")
                for step_file in step_files:
                    try:
                        # Extract step number from filename (e.g., "0_step_report.html" -> "0")
                        step_num = step_file.name.split('_')[0]
                        with open(step_file, 'r') as f:
                            content = f.read()
                            research_results[step_num] = content
                    except Exception as e:
                        logger.error(f"Error reading step file {step_file} for crew {crewid}: {e}")
        
        # Get final report - first try the standard file
        final_report_file = crew_dir / 'final_report.txt'
        final_report = ""
        
        if final_report_file.exists():
            try:
                with open(final_report_file, 'r') as f:
                    final_report = f.read()
            except Exception as e:
                logger.error(f"Error reading final report for crew {crewid}: {e}")
        
        # If no final report found, check for final_final_report.html
        if not final_report:
            final_html_file = crew_dir / 'final_final_report.html'
            if final_html_file.exists():
                try:
                    with open(final_html_file, 'r') as f:
                        final_report = f.read()
                except Exception as e:
                    logger.error(f"Error reading final HTML report for crew {crewid}: {e}")
        
        # If we still don't have a research plan but have step reports, create a dummy plan
        if not research_plan and research_results:
            research_plan = {}
            for step_num in sorted(research_results.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
                research_plan[f"step{step_num}"] = f"Research step {step_num}"
        
        # If we don't have a research topic but have results, create a dummy topic
        if not research_topic and (research_results or final_report):
            research_topic = "Research topic (recovered from results)"
        
        return jsonify({
            'research_topic': research_topic,
            'research_plan': research_plan,
            'research_results': research_results,
            'final_report': final_report,
            'entities': entities,  # Include entities separately
            'crewid': crewid
        })
    except Exception as e:
        logger.exception(f"Error retrieving research for crew {crewid}")
        return jsonify({'error': str(e), 'crewid': crewid}), 500

@app.route('/settings', methods=['GET'])
def get_settings():
    return jsonify({
        'openai_api_key': getenv('OPENAI_API_KEY', ''),
        'openai_model_name': getenv('OPENAI_MODEL_NAME', ''),
        'lm_studio_url': getenv('LM_STUDIO_URL', ''),
        'serper_api_key': getenv('SERPER_API_KEY', '')
    })

@app.route('/settings', methods=['POST'])
def update_settings():
    data = request.json
    env_path = '.env'
    
    # Update environment variables
    if 'openai_api_key' in data:
        set_key(env_path, 'OPENAI_API_KEY', data['openai_api_key'])
        os.environ['OPENAI_API_KEY'] = data['openai_api_key']
    
    if 'openai_model_name' in data:
        set_key(env_path, 'OPENAI_MODEL_NAME', data['openai_model_name'])
        os.environ['OPENAI_MODEL_NAME'] = data['openai_model_name']
    
    if 'lm_studio_url' in data:
        set_key(env_path, 'LM_STUDIO_URL', data['lm_studio_url'])
        os.environ['LM_STUDIO_URL'] = data['lm_studio_url']
    
    if 'serper_api_key' in data:
        set_key(env_path, 'SERPER_API_KEY', data['serper_api_key'])
        os.environ['SERPER_API_KEY'] = data['serper_api_key']
    
    return jsonify({'status': 'success'})

@app.route('/check_settings')
def check_settings():
    serper_key = getenv('SERPER_API_KEY', '')
    openai_key = getenv('OPENAI_API_KEY', '')
    openai_model = getenv('OPENAI_MODEL_NAME', '')
    lm_studio_url = getenv('LM_STUDIO_URL', '')
    
    # Check if we have Serper API key AND either (OpenAI credentials OR LM Studio URL)
    settings_valid = (
        serper_key and 
        (
            (openai_key and openai_model) or 
            lm_studio_url
        )
    )
    
    return jsonify({'settings_valid': settings_valid})

@app.route('/current_crewid', methods=['GET'])
def get_current_crewid():
    current_crewid = CrewID.get_crewid()
    return jsonify({"crewid": current_crewid})

@app.route('/set_crewid/<crewid>', methods=['POST'])
def set_crewid(crewid):
    try:
        CrewID.set_crewid(crewid)
        return jsonify({"status": "success", "crewid": crewid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    """Generate a PDF using xhtml2pdf based on the content provided."""
    try:
        data = request.json
        title = data.get('title', 'Research Step')
        content = data.get('content', '')
        step_number = data.get('step_number', 1)
        
        # Determine if this is a complete report
        is_complete_report = step_number == 'complete'
        
        # Create HTML content with appropriate styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: a4;
                    margin: 1cm;
                }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    line-height: 1.6; 
                    color: #333;
                }}
                h1 {{ 
                    color: #2c3e50; 
                    border-bottom: 1px solid #eee; 
                    padding-bottom: 10px;
                    font-size: 24px;
                }}
                h2 {{ 
                    color: #3498db; 
                    margin-top: 20px;
                    font-size: 20px;
                }}
                h3 {{ 
                    color: #2980b9;
                    font-size: 18px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .citation {{
                    font-size: 12px;
                    color: #7f8c8d;
                    margin-top: 5px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    margin-top: 30px;
                    color: #7f8c8d;
                }}
                ul, ol {{
                    margin-left: 20px;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            {content}
            <div class="footer">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </body>
        </html>
        """
        
        # Save the PDF generation prompt
        from utils.capabilities.File import File
        from utils.crewid import CrewID
        crewid = CrewID.get_crewid()
        
        pdf_prompt = f"""
        PDF Generation for: {title}
        Step Number: {step_number}
        Is Complete Report: {is_complete_report}
        
        HTML Content Template:
        {html_content}
        """
        
        File.save_prompt(crewid, f"pdf_generation_{step_number}", pdf_prompt)
        
        # Create a temporary file to store the HTML
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as html_file:
            html_file.write(html_content.encode('utf-8'))
            html_file_path = html_file.name
        
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
            pdf_file_path = pdf_file.name
        
        # Convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=open(pdf_file_path, "wb")
        )
        
        if pisa_status.err:
            os.unlink(html_file_path)
            os.unlink(pdf_file_path)
            return jsonify({"status": "error", "message": "PDF generation failed"}), 500
        
        # Read the PDF file
        with open(pdf_file_path, 'rb') as pdf:
            pdf_data = pdf.read()
        
        # Clean up temporary files
        os.unlink(html_file_path)
        os.unlink(pdf_file_path)
        
        # Determine filename based on whether it's a complete report
        if is_complete_report:
            filename = "complete_research_report.pdf"
        else:
            filename = f"research_step_{step_number}.pdf"
        
        # Create response with PDF data
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run in test mode with mock data')
    args = parser.parse_args()
    
    # Update test_mode using the new function from config
    logger.debug(f"Setting mode to {'test' if args.test else 'production'} mode")
    set_test_mode(args.test)
    
    # Import test_mode again after setting it
    from config import test_mode
    
    app.run(debug=True)