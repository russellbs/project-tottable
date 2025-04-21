import openai

# Initialize OpenAI client with your API key
client = openai.OpenAI(api_key="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")  # Initialize client

# Fetch and list all available models
models = client.models.list()

print("✅ Available Models:")
for model in models.data:
    print(model.id)
