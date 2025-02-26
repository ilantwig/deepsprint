<div style="display: flex; justify-content: space-between; gap: 5px;">
    <picture>
       <img src="./static/rtx-compare.png" width="45%" style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    </picture>
    <picture>
       <img src="./static/results.png" width="45%" style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    </picture>
</div>

# DeepSprint

DeepSprint supercharges your research with AI, helping you dive deep into any topic in record time. Born from my own need to accelerate research workflows at [Navan](https://www.navan.com), I built this tool to make thorough research accessible to everyone.

# Quick start - using OpenAI models
With pip (Python<=3.12):

```bash
git clone https://github.com/ilantwig/deepsprint.git
cd deepsprint
pip install -r requirements.txt
python app.py
```
You will need to have a Serper API key and either LM-Studio URL or OpenAI KEY and Model Name.
<picture>
    <img src="./static/settings.png" width="100%" style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
</picture>

For permenant configuration, add your API keys for the provider you want to use to your `.env` file.

```env
OPENAI_API_KEY=
OPENAI_MODEL_NAME=
SERPER_API_KEY=
LM_STUDIO_BASE_URL="http://localhost:1234/v1"
```

# Using LM Studio models
Make sure you started LM Studio server and it's running.
<picture>
   <img src="./static/lm-studio-server-mac.jpg"   style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
</picture>

## Running in test mode

```bash
python app.py --test
```
<picture>
   <img src="./static/test.png"  width="50%" height = "50%" style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
</picture>

## Features

- Rapid deep research capabilities
- Support for both OpenAI and local LLM models via LM Studio
- Flexible API integration with SerperAPI for web searches
- Flask-based server architecture

## Prerequisites

- Python 3.11
- pip (Python package installer)
- LM Studio (optional, for local model usage)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/ilantwig/deepsprint.git
    cd deepsprint
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Configure environment variables:
    - Copy `.env.template` to `.env`
    - Fill in the required API keys and configurations:
    ```env
    # OpenAI Configuration
    OPENAI_API_KEY=your_openai_api_key
    OPENAI_MODEL=gpt-4

    # SerperAPI Configuration
    SERPER_API_KEY=your_serper_api_key

    # LM Studio Configuration (Optional)
    LM_STUDIO_BASE_URL=your_lm_studio_endpoint
    ```

## Project Structure

```deepsprint/
├── _pycache_/        # Python cache directory
├── output/           # Output files directory
├── prompts/          # Prompt templates
├── templates/        # HTML/UI templates
├── utils/            # Utility functions
├── .env             # Environment variables
├── .env.template    # Template for environment variables
├── .gitignore       # Git ignore rules
├── app.py           # Main Flask application
├── LICENSE          # License file
├── README.md        # This file
├── requirements.txt  # Python dependencies
└── research_coordinator.py  # Research coordination logic
```

## Usage

1. Start the Flask server:
    ```bash
    python app.py
    ```

2. Access the application through your web browser at `http://localhost:5000` (or the configured port)

### Using with OpenAI
- Make sure you have set your OpenAI API key in the `.env` file
- The application will automatically use the specified OpenAI model for processing

### Using with LM Studio
1. Start LM Studio and load your desired model
2. Copy the provided endpoint URL from LM Studio
3. Update the `LM_STUDIO_BASE_URL` in your `.env` file
4. The application will use your local model through LM Studio

## Configuration Options

- `OPENAI_MODEL`: Specify which OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
- `LM_STUDIO_BASE_URL`: The endpoint URL for your local LM Studio instance
- Additional configuration options can be found in `.env.template`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Support

For issues, questions, or suggestions, please [open an issue](https://github.com/ilantwig/deepsprint/issues) on GitHub.

## Acknowledgments

- OpenAI for their powerful language models
- SerperAPI for search capabilities
- The LM Studio team for local model support

## Author

Ilan Twig, CTO and Co-founder of [Navan](https://www.navan.com)
