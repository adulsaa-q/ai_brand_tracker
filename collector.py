from google import genai
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
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
print(f"timestamp : {timestamp}")
print(f"model     : {model_name}")
print(f"prompt    : {prompt}")
print(response.text)

# brand in response
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
rows = []
for brand in allnii_competitors:
    rows.append({
        "timestamp": timestamp,
        "model": model_name,
        "prompt": prompt,
        "brand": brand,
        "mentioned": brand in found_brands  # True or False
    })
df = pd.DataFrame(rows)
df.to_csv("results.csv", mode="a", header=not os.path.exists("results.csv"), index=False)
print("\n ---Data saved to results.csv---")