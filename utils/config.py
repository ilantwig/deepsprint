import os
from enum import Enum
from pathlib import Path
from langchain_openai import ChatOpenAI

class ModelConfig:
    DEFAULT_TEMPERATURE = 0.7
    open_ai_model=os.getenv("OPENAI_MODEL_NAME")
    lm_studio_base_url=os.getenv("LM_STUDIO_URL")
    @classmethod
    def get_model(cls, model_name=None, temperature=DEFAULT_TEMPERATURE):
        if os.getenv("OPENAI_API_KEY"):
            print(f"config.py:: Using OpenAI model: {ModelConfig.open_ai_model}")
            return ChatOpenAI(model_name=model_name or ModelConfig.open_ai_model)
        else:
            print(f"Using LLM Studio model via: {ModelConfig.lm_studio_base_url}")
            return ChatOpenAI(base_url=os.getenv("LM_STUDIO_URL"), api_key="lm-studio")
    


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