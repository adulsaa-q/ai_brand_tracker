from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# ส่วนที่ 1 — กล่องเก็บ brand
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

# ส่วนที่ 2 — ถาม Gemini
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="ซื้อของออนไลน์ที่ไหนดีในไทย?"
)

print("---Gemini Response---")
print(response.text)

# ส่วนที่ 3 — ค้นหา brand ใน response ← เพิ่มตรงนี้!
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