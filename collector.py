from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

allnii_competitors = [
    "Konvy",
    "EVEANDBOY",
    "Beautrium",
    "Sephora Thailand",
    "Watsons Thailand",
    "Boots Thailand",
]

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="แนะนำ supplement ยี่ห้อดีๆ หน่อย"
)

print(response.text)

# หา brand ใน response
found_brands = []
for brand in allnii_competitors:
    if brand.lower() in response.text.lower():
        found_brands.append(brand)

print("พบแบรนด์:", found_brands)