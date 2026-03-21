from google import genai
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

#context to promt
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
model_name = "gemini-2.5-flash"
prompt = "ซื้อของออนไลน์ที่ไหนดีในไทย?"

# brand box
allnii_competitors = [
    "Allnii",
    "Konvy",
    "EVEANDBOY",
    "Beautrium",
    "Sephora",
    "Watsons",
    "Boots",
    "Lazada",
    "Shopee"
]
# prompt
response = client.models.generate_content(
    model=model_name,
    contents=prompt
)

print("---Gemini Response---")
print(response.text)

found_brands = []
for brand in allnii_competitors:
    if brand.lower() in response.text.lower():
        found_brands.append(brand)

print("\n---Platform Mentioned---")
if found_brands:
    for brand in found_brands:
        print(f"mentioned: {brand}")
else:
    print("platform not mentioned")