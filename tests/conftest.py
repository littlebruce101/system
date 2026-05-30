import os

# Set a dummy API key so the OpenAI client can be instantiated at import time
# without real credentials. All tests that use the client mock it out anyway.
os.environ.setdefault("OPENAI_API_KEY", "test-dummy-key")
