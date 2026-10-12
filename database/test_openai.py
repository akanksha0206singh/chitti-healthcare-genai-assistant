import os
from openai import OpenAI

# Create the OpenAI client.
# It automatically reads OPENAI_API_KEY from the environment.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-6-luna",
    input="Say 'OpenAI connection successful!'"
)

print(response.output_text)