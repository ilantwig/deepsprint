from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from research_coordinator import build_research_plan, deep_sprint_topic
import json

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
    research_steps = request.json.get('research_steps', [])
    
    def generate():
        previous_result = ""  # Track previous result for context

        for i, step in enumerate(research_steps):
            try:
                result = deep_sprint_topic(step, previous_result)  # Pass previous result
                previous_result = result['summary']  # Update previous result
                # Ensure each line is a complete, valid JSON object
                response_data = json.dumps({
                    'step': i + 1,
                    'result': result['summary'],
                    'execution_time': result['execution_time']
                })
                yield f"{response_data}\n"
            except Exception as e:
                response_data = json.dumps({
                    'step': i + 1,
                    'error': str(e)
                })
                yield f"{response_data}\n"

    return Response(
        stream_with_context(generate()),
        mimetype='application/x-ndjson'  # Changed to ndjson format
    )

if __name__ == '__main__':
    app.run(debug=True)
