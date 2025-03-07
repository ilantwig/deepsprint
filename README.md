<picture>
    <img src="./static/rtx-compare.png" width="90%" style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
</picture>

<h1 align="center">Let the AI do the research 🤖</h1>

[![GitHub followers](https://img.shields.io/github/followers/ilantwig?label=Follow)](https://github.com/ilantwig)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/itwig)
[![Twitter](https://img.shields.io/twitter/follow/itwig)](https://twitter.com/itwig)

# DeepSprint
A quick UI-based tool to help you do deep research.  Nothing fancy, just a simple tool to help you do deep research.

# Quick start
Requires Python>=3.10 and <=3.12!!

```bash
git clone https://github.com/ilantwig/deepsprint.git
cd deepsprint
pip install -r requirements.txt
python app.py
```
You can also use conda to install the dependencies.
```bash
conda create -n deepsprint python=3.11
conda activate deepsprint
pip install -r requirements.txt
python app.py
```

Access the application through your web browser at `http://localhost:5000` (or the configured port)

You will need to have a Serper API key and either LM-Studio URL or OpenAI KEY and Model Name.
<picture>
    <img src="./static/settings.png" width="90%" style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
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
   <img src="./static/lm-studio-server-mac.jpg" width="90%"  style="border: 4px solid #ddd; border-radius: 8px; padding: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
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
- Browse through the research results as well as past reports in the browser
- Flask-based server architecture

## Prerequisites

- Python 3.11
- pip (Python package installer)
- LM Studio (optional, for local model usage)


### Using with OpenAI
- Make sure you have set your OpenAI API key in the `.env` file
- The application will automatically use the specified OpenAI model for processing

### Using with LM Studio
1. Start LM Studio and load your desired model
2. Copy the provided endpoint URL from LM Studio
3. Update the `LM_STUDIO_BASE_URL` in your `.env` file
4. The application will use your local model through LM Studio

## Contributing

Do whatever you want with it.

## License

MIT License

## Support

For issues, questions, or suggestions, please [open an issue](https://github.com/ilantwig/deepsprint/issues) on GitHub.
I am busy, so I may not respond to issues.


## Author

Ilan Twig, CTO and Co-founder of [Navan](https://www.navan.com)
