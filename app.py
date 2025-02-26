import warnings
import logging
# Filter out Pydantic's deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", ".*Pydantic V1.*")
warnings.filterwarnings("ignore", ".*PydanticDeprecatedSince20.*")

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
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

logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

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

@app.route('/', methods=['GET', 'POST'])
def index():
    global test_mode
    # Import test_mode again to get the latest value
    from config import test_mode
    print(f"test_mode: {test_mode}")
    research_plan = None
    research_results = None
    model_status = get_model_status()
    
    if request.method == 'POST':
        research_topic = request.form['research_topic']
        research_plan = build_research_plan(research_topic)
        return render_template('index.html', 
                             research_plan=research_plan, 
                             research_topic=research_topic,
                             research_results=research_results,
                             test_mode=test_mode,
                             model_status=model_status)
    return render_template('index.html', 
                         research_plan=research_plan,
                         research_results=research_results,
                         test_mode=test_mode,
                         model_status=model_status)

@app.route('/regenerate', methods=['POST'])
def regenerate_plan():
    research_topic = request.form['research_topic']
    research_plan = build_research_plan(research_topic)
    return jsonify(research_plan=research_plan, 
                  research_results=None, 
                  test_mode=test_mode)

@app.route('/execute_deep_sprint', methods=['POST'])
def execute_deep_sprint():
    research_steps = request.json.get('research_steps', [])
    result_queue = Queue()
    results_container = {'all_results': ''}

    def process_step(step, step_num):
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
                result = deep_sprint_topic(step, step_num)
            
            result_dict = {
                'step': step_num + 1,
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
        for i, step in enumerate(research_steps):
            thread = Thread(target=process_step, args=(step, i))
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
