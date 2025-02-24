from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from research_coordinator import build_research_plan, deep_sprint_topic, generate_final_report
import json
from threading import Thread
from queue import Queue
from utils.crewid import CrewID
from pathlib import Path
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    research_plan = None
    research_results = None
    if request.method == 'POST':
        research_topic = request.form['research_topic']
        research_plan = build_research_plan(research_topic)
        # Pass the original topic, plan, and results to the template
        return render_template('index.html', 
                             research_plan=research_plan, 
                             research_topic=research_topic,
                             research_results=research_results)
    return render_template('index.html', 
                         research_plan=research_plan,
                         research_results=research_results)

@app.route('/regenerate', methods=['POST'])
def regenerate_plan():
    research_topic = request.form['research_topic']
    research_plan = build_research_plan(research_topic)
    return jsonify(research_plan=research_plan, research_results=None)

@app.route('/execute_deep_sprint', methods=['POST'])
def execute_deep_sprint():
    CrewID.regenerate_crewid()
    research_steps = request.json.get('research_steps', [])
    result_queue = Queue()
    # Move all_results to a mutable container to avoid global variable issues
    results_container = {'all_results': ''}

    def process_step(step, step_num):
        try:
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

@app.route('/load_research/<crewid>', methods=['GET'])
def load_research(crewid):
    try:
        output_dir = Path('output') / crewid
        if not output_dir.exists():
            return jsonify({'error': 'Research not found'}), 404
            
        research_data = {
            'steps': [],
            'results': [],
            'final_report': ''
        }
        
        # Load step reports
        step = 0
        while True:
            step_file = output_dir / f"{step}_step_report.html"
            if not step_file.exists():
                break
            with open(step_file, 'r', encoding='utf-8') as f:
                research_data['results'].append(f.read())
            step += 1
            
        # Load final reports
        final_report = []
        
        # Try loading regular final report
        final_report_file = output_dir / "final_report.html"
        if final_report_file.exists():
            with open(final_report_file, 'r', encoding='utf-8') as f:
                final_report.append(f.read())
                
        # Try loading fina final report
        fina_final_report_file = output_dir / "fina_final_report.html"
        if fina_final_report_file.exists():
            with open(fina_final_report_file, 'r', encoding='utf-8') as f:
                final_report.append(f.read())
        
        # Combine final reports if both exist
        research_data['final_report'] = '<br><br>'.join(final_report)
                
        return jsonify(research_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
