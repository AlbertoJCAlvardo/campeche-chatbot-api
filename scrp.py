import google.generativeai as genai

# If you're setting an API key directly
# genai.configure(api_key="YOUR_API_KEY")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model: {m.name}, Supported Methods: {m.supported_generation_methods}")
