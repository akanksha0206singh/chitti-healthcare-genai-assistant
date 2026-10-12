from google import genai

print("Starting Gemini test...")

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Say exactly: Gemini connection successful!"
)

print("Gemini response:")
print(response.text)