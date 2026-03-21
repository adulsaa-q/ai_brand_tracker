# 🔍 AI Brand Visibility Tracker

> **Track how AI talks about your brand** — inspired by [Peec.ai](https://peec.ai)

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange?logo=google)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

---

## 💡 What is this?

When people ask AI **"Where should I shop online in Thailand?"** — does your brand show up?

This tool automatically tracks **which brands AI mentions**, **how often**, **in what order**, and **with what sentiment** — giving you actionable insights to improve your brand's presence in AI-generated answers.

This is called **GEO (Generative Engine Optimization)** — the new SEO for the AI era.

---

## 🎯 Inspired by Peec.ai

| Metric | Description |
|--------|-------------|
| 📊 **Visibility** | Is your brand mentioned? (True/False) |
| 🏆 **Position** | Where does your brand appear in the response? |
| 🥇 **Rank** | What order is your brand mentioned? (1st, 2nd, 3rd...) |
| 💬 **Sentiment** | Is AI saying positive, neutral, or negative things? |
| 📝 **Reason** | What specifically does AI say about your brand? |

---

## 📸 Example Output

```
timestamp,model,prompt,brand,mentioned,position,rank,sentiment,reason
2026-03-21 09:00,gemini-2.5-flash,ซื้อของออนไลน์ที่ไหนดี?,Lazada,True,241,1,positive,สินค้าหลากหลาย โปรโมชั่นเยอะ
2026-03-21 09:00,gemini-2.5-flash,ซื้อของออนไลน์ที่ไหนดี?,Shopee,True,590,2,positive,มีเกมสะสมคอยน์ ส่งฟรีบ่อย
2026-03-21 09:00,gemini-2.5-flash,ซื้อของออนไลน์ที่ไหนดี?,Allnii,False,-1,0,not_mentioned,ไม่ถูกพูดถึง
```

> **Key insight:** Allnii is not mentioned by AI at all — a clear signal to create more AI-visible content!

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/ai-brand-tracker.git
cd ai-brand-tracker
```

### 2. Set up environment
```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
pip install -r requirements.txt
```

### 3. Add your API key
```bash
# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```
Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com)

### 4. Configure your brands & prompts
```python
# config.py — edit this file only, no need to touch collector.py

BRANDS = [
    "YourBrand",      # ← Add your brand here
    "Competitor1",
    "Competitor2",
]

PROMPTS = [
    "ซื้อของออนไลน์ที่ไหนดีในไทย?",
    "แพลตฟอร์มช้อปปิ้งออนไลน์ไหนดีที่สุด?",
    # Add more prompts your customers might ask
]
```

### 5. Run it!
```bash
python collector.py
```

---

## 📁 Project Structure

```
ai-brand-tracker/
│
├── collector.py        # 🤖 Main script — collects & analyzes data
├── config.py           # ⚙️  Configure brands & prompts (edit this!)
├── results.csv         # 📊 Output data (auto-generated)
├── requirements.txt    # 📦 Dependencies
├── .env                # 🔑 API keys (never commit this!)
└── .gitignore          # 🚫 Protects sensitive files
```

---

## 📊 Data Collected

Each run collects the following for every brand × prompt combination:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | datetime | When the data was collected |
| `model` | string | AI model used (e.g. gemini-2.5-flash) |
| `prompt` | string | The question asked to AI |
| `brand` | string | Brand name being tracked |
| `mentioned` | boolean | Whether AI mentioned this brand |
| `position` | integer | Character position in response (-1 = not found) |
| `rank` | integer | Order of mention (1 = first mentioned) |
| `sentiment` | string | positive / neutral / negative / not_mentioned |
| `reason` | string | Why AI feels this way about the brand |

---

## 🔧 Tech Stack

| Tool | Purpose |
|------|---------|
| 🐍 Python 3.11+ | Core language |
| 🤖 Google Gemini API | AI responses |
| 🐼 pandas | Data processing & CSV export |
| 🔐 python-dotenv | Secure API key management |
| 📊 Power BI / Excel | Dashboard visualization |

---

## 💼 Business Use Case

This tool helps marketing teams answer:

- ❓ **"Does AI recommend our brand?"**
- ❓ **"Which competitors does AI favor?"**
- ❓ **"What does AI say is good/bad about us?"**
- ❓ **"Which prompts give us the best visibility?"**

Then **take action** based on data:
- 🔴 Not mentioned → Create content that AI can reference
- 🟡 Negative sentiment → Address the specific issue AI highlights
- 🟢 Positive sentiment → Double down on what's working

---

## 📈 Roadmap

- [x] Brand mention tracking
- [x] Position & rank analysis
- [x] Sentiment + reason analysis
- [x] Multi-prompt support
- [x] CSV export
- [ ] Power BI dashboard
- [ ] Scheduled auto-runs
- [ ] Multi-model support (GPT-4, Claude)
- [ ] Source/citation tracking

---

## 🙏 Credits

Inspired by [Peec.ai](https://peec.ai) — the leading AI Search Analytics platform.

Built as a portfolio project to demonstrate **Data Engineering** skills:
Python • API Integration • Data Pipeline • Analytics

---

## 📄 License

MIT License — free to use, please credit the author.

---

<p align="center">
  Made with ❤️ for the GEO era
  <br>
  <em>Because the future of search is AI-powered</em>
</p>
