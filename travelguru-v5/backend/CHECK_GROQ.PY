from groq import Groq
import os

# Initialize client with your API key
client = Groq(api_key="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")

# List available models
models = client.models.list()

# Print them out
for model in models.data:
    print(model.id)