import os
from enum import Enum
from pathlib import Path
from langchain_openai import ChatOpenAI

class ModelConfig:
    DEFAULT_TEMPERATURE = 0.7
    
    @classmethod
    def get_model(cls, model_name=None, temperature=DEFAULT_TEMPERATURE):
        # Get latest environment variables but don't require them
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_model = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        lm_studio_url = os.getenv("LM_STUDIO_URL")
        
        # Return None if no configuration is available yet
        if not any([openai_api_key, lm_studio_url]):
            return None
        
        if openai_api_key and openai_api_key.startswith('sk-'):
            print(f"config.py:: Using OpenAI model: {openai_model}")
            return ChatOpenAI(
                model_name=model_name or openai_model,
                temperature=temperature
            )
        elif lm_studio_url:
            print(f"Using LLM Studio model via: {lm_studio_url}")
            return ChatOpenAI(
                base_url=lm_studio_url,
                api_key="not-needed",  # LM Studio doesn't check the API key
                model_name="local-model",  # Use a placeholder model name
                temperature=temperature
            )
        else:
            raise ValueError("No valid model configuration found. Please set either OPENAI_API_KEY or LM_STUDIO_URL")
    


default_model = ModelConfig.get_model()

# class Model(Enum):
#     GPT_4o = "gpt-4o"
#     GPT_4o_mini = "gpt-4o-mini"
#     LLAMA_3 = "Llama3"

class Config:
    class Path:
        APP_HOME = Path(os.getenv("APP_HOME", Path(__file__).parent.parent))
        DATA_DIR = APP_HOME / "data"
        OUTPUT_DIR = APP_HOME / "output"
        TOOLS_FOLDER = APP_HOME / "lib/capabilities"
    
    USE_THREADS=False #determines if dimensions analysis will run in parallel or not.

    REPORTS_FORMAT="txt" #"md" "html" "json" "txt"


    # MODEL = Model.LLAMA_3