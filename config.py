import yaml

with open("settings.yaml", "r", encoding="utf-8") as f:
    settings = yaml.safe_load(f)

MODEL_NAME = settings["model"]
BRANDS = settings["brands"]
PROMPTS = [
    {
        "text": p["text"] if isinstance(p, dict) else p,
        "category": p.get("category") if isinstance(p, dict) else None
    }
    for p in settings["prompts"]
]