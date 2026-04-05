# Pre-Submission Checklist
## Please confirm before submitting.

- I've read the sample inference.py and have followed it strictly

- Environment variables are present in inference.py
API_BASE_URL, MODEL_NAME, HF_TOKEN - optional:
LOCAL IMAGE NAME when using from_docker_image()

- Defaults are set only for API_BASE_URL and MODEL_NAME (not HF_TOKEN)
```
API BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
MODEL NAME = os.getenv("MODEL_NAME", "<your-active-model>")
HF TOKEN = os.getenv("HF_TOKEN")

# Optional - if you use from_docker_image():
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
```

- All LLM calls use the OpenAl client configured via these variables from openai import OpenAI

- Stdout logs follow the required structured format (START/STEP/END) exactly