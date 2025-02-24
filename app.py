from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from research_coordinator import build_research_plan, deep_sprint_topic
import json
from threading import Thread
from queue import Queue

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
    result_queue = Queue()

    def process_step(step, step_num):
        try:
            result = deep_sprint_topic(step)
            result_queue.put({
                'step': step_num + 1,
                'result': result['summary'],
                'execution_time': result['execution_time']
            })
        except Exception as e:
            result_queue.put({
                'step': step_num + 1,
                'error': str(e)
            })

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

    return Response(
        stream_with_context(generate()),
        mimetype='application/x-ndjson'
    )

if __name__ == '__main__':
    app.run(debug=True)
