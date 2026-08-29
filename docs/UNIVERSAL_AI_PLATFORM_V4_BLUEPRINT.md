# 🏛️ UNIVERSAL AI MARKET & DECISION INTELLIGENCE PLATFORM (V4.0)
## Complete Architecture Blueprint, Universal Multi-Vertical Engine & Self-Service UI/UX Specification

> **Author:** Adul Saa (Q)  
> **Document Version:** 4.0.0-PROD  
> **Target Status:** Full-Stack Enterprise Self-Service SaaS Architecture  
> **Design Language:** Architectural Monochromatic Luxury (Style Q // `#F2F0EF`, `#C9C8C7`, `#949392`, `#66615E`, Black)

---

# 1. EXECUTIVE VISION & PARADIGM SHIFT

### 🎯 The Core Problem of V1–V3
* **V1–V3:** ถูกสร้างเป็นชุดสคริปต์วิเคราะห์เฉพาะกลุ่ม (Beauty E-Commerce) และต้องสั่งงานผ่าน Terminal CLI (`python src/cli.py run`) ทำให้ **ผู้บริหาร, ทีมการตลาด, นักกลยุทธ์, หรือลูกค้าทั่วไปใช้งานจริงไม่ได้ด้วยตนเอง**
* **ข้อจำกัดเรื่องอุตสาหกรรม:** ผูกติดอยู่กับแบรนด์อีคอมเมิร์ซ 9 แบรนด์ในไฟล์ YAML หากต้องการวิเคราะห์วงการอื่น (เช่น รถยนต์ไฟฟ้า EV, ธนาคาร, คอนโด, โรงพยาบาล) ต้องเข้าไปเขียนโค้ดแก้

### 🚀 The V4.0 Transformation (Universal Zero-Terminal Platform)
1. **Zero-Terminal Self-Service UI/UX:** ผู้ใช้สามารถทำทุกอย่างได้ผ่านหน้าเว็บ 100% โดยไม่ต้องเปิด Terminal หรือแตะโค้ดแม้แต่บรรทัดเดียว
2. **Universal Multi-Vertical Engine (Any Industry, Any Brand):** รองรับการสร้างกลุ่มอุตสาหกรรมและรายชื่อแบรนด์คู่แข่งได้อย่างอิสระไม่จำกัด (EV, FinTech, Real Estate, Hospitals, F&B, Travel)
3. **1-Click Live AI Scanner with Real-Time Progress Stream:** เลือกรันโมเดล AI (Gemini 2.5 Flash, Tavily Grounding, OpenRouter, Mock) ผ่านหน้าเว็บ พร้อมแถบสถานะวิ่งสด 0%–100%
4. **Lightweight Full-Stack Architecture:** ขับเคลื่อนด้วย **FastAPI Backend Micro-Engine + DuckDB Star Schema Lakehouse + Pure Vanilla/Tailwind/Chart.js Frontend** (Zero heavy build steps, Zero complex setups)

---

# 2. SYSTEM ARCHITECTURE & DATA FLOW

```mermaid
graph TD
    subgraph Frontend [Executive Web Interface - Architectural Luxury]
        UI_Header[Header: Industry Selector & Global Controls]
        UI_Wizard[Modal: + Add/Edit Industry & Brand Wizard]
        UI_Scanner[Modal: 1-Click AI Scan Launcher]
        UI_Progress[Live Progress Tracker & Log Stream]
        UI_Dashboard[5-Module Executive Analytics Dashboard]
    end

    subgraph Backend [FastAPI Micro-Engine: src/api.py]
        API_Verts[GET/POST /api/v1/verticals]
        API_Scan[POST /api/v1/scan - Background Tasks]
        API_Stream[GET /api/v1/scan/{task_id}/progress - SSE]
        API_Metrics[GET /api/v1/metrics/{vertical_id}]
        API_Export[GET /api/v1/export/{vertical_id}]
    end

    subgraph CoreEngine [Intelligence Orchestration Engine]
        Gen_Univ[Universal Industry Query Generator]
        Factory_Eng[Multi-Engine Observation Layer]
        Parser_Pyd[Single-Pass Pydantic Extraction]
    end

    subgraph StorageLakehouse [Zero-Cost Partitioned Lakehouse]
        Duck_Store[(DuckDB Star Schema: dim_brand, fact_obs, fact_mention, fact_cite)]
        SQLite_Store[(SQLite Transactional Store)]
    end

    %% Interactions
    UI_Wizard -->|Create Vertical| API_Verts
    UI_Scanner -->|Trigger Scan| API_Scan
    API_Scan --> Gen_Univ
    Gen_Univ --> Factory_Eng
    Factory_Eng --> Parser_Pyd
    Parser_Pyd --> Duck_Store & SQLite_Store
    API_Scan -.->|Stream Progress| API_Stream -.-> UI_Progress
    Duck_Store -->|Query Analytics JSON| API_Metrics --> UI_Dashboard
    UI_Header -->|Switch Industry| UI_Dashboard
```

---

# 3. UNIVERSAL MULTI-VERTICAL ENGINE SPECIFICATION

### 3.1 การสร้าง Prompt Universe อัตโนมัติสำหรับทุกอุตสาหกรรม (Domain-Agnostic Synthesis)
เมื่อผู้ใช้สร้างอุตสาหกรรมใหม่ ระบบจะดึงแกนคำถามตาม **Consumer Intent Taxonomy** 6 มิติหลัก:

```
┌────────────────────────────────────────────────────────────────────────┐
│ UNIVERSAL CONSUMER INTENT TAXONOMY (6 CORE PILLARS)                    │
├────────────────────────────────────────────────────────────────────────┤
│ 1. PROMOTION & VALUE    : แคมเปญส่วนลด, ความคุ้มค่า, โปรโมชั่นล่าสุด   │
│ 2. TRUST & AUTHENTICITY : ความน่าเชื่อถือ, ประกันศูนย์, ความปลอดภัย    │
│ 3. PRODUCT & VARIETY    : ความหลากหลาย, สเปก, รุ่นนำเข้า, ความครบครัน  │
│ 4. SERVICE & SPEED      : ความรวดเร็วในการส่ง/บริการ, การเคลม, CS       │
│ 5. PAYMENT & FINANCING  : การผ่อนชำระ, 0%, ดอกเบี้ย, ความสะดวกในการจ่าย │
│ 6. SPECIALIZED INTENT   : คำถามเฉพาะกลุ่ม, ของขวัญ, การใช้งานทางเทคนิค │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Pre-Configured Benchmark Verticals (6 อุตสาหกรรมหลักของไทย)

1. **`ecommerce_retail_th` (Beauty & E-Commerce):**
   - *Brands:* Shopee, Lazada, Watsons, Sephora, Beautrium, EVEANDBOY, Konvy, Boots, Allnii
   - *Key Levers:* Double Day codes, Authentic Mall guarantee, Gift wrapping, Return policy
2. **`ev_automotive_th` (Electric Vehicles & Auto):**
   - *Brands:* BYD, Tesla, MG, GAC AION, Changan, Great Wall Motor (GWM), Toyota, Honda
   - *Key Levers:* 8-Year Battery Warranty, DC Fast Charging Network, Resale Value Guarantee, Mobile Service
3. **`banking_fintech_th` (Banking & Digital FinTech):**
   - *Brands:* KBank, SCB, Krungthai (KTB), Bangkok Bank (BBL), KKP, TrueMoney, Dime, Make by KBank
   - *Key Levers:* High-yield digital savings, Point reward multipliers, Fast loan approval, App uptime 99.9%
4. **`real_estate_th` (Property & Condominiums):**
   - *Brands:* Sansiri, AP Thailand, Land & Houses (LH), SC Asset, Supalai, Ananda
   - *Key Levers:* BTS/MRT Proximity, Juristic Management Quality, Construction defect warranty, Free transfer fee
5. **`hospital_healthcare_th` (Private Hospitals & Healthcare):**
   - *Brands:* Bumrungrad, BDMS (Bangkok Hospital), Samitivej, MedPark, Thonburi Hospital, Phyathai
   - *Key Levers:* JCI Accreditation, Comprehensive Check-up Packages, English/Arabic CS, Specialist Doctor Consensus
6. **`fnb_coffee_th` (F&B & Coffee Retail Chains):**
   - *Brands:* Cafe Amazon, Starbucks Thailand, Inthanin, PunThai, Flash Coffee, TrueCoffee
   - *Key Levers:* Specialty roast beans, Drive-thru density, Member reward points, Bakery freshness

---

# 4. FRONTEND UI/UX ARCHITECTURE (ARCHITECTURAL LUXURY - STYLE Q)

### 4.1 Design Tokens
* **Base Canvas:** `#F2F0EF` (Warm Bone Concrete)
* **Primary Surface:** `#FAF9F8`
* **Secondary Surface / Ledger:** `#E6E4E2`
* **Hairline Dividers:** `1px solid #C9C8C7`
* **Tertiary Faint Metadata:** `#949392`
* **Secondary Analytical Ink:** `#66615E`
* **Primary High-Contrast Ink:** `#111110` / `#000000`
* **Typography:** `Newsreader` (Editorial Serif Headlines), `Plus Jakarta Sans` (UI & Tabular Nums), `Prompt` (Thai Body)

### 4.2 Web Control Center Modules

```
[Web Application Structure]
├── 1. Top Executive Masthead & Controls
│   ├── Title: "THAILAND AI MARKET INTELLIGENCE"
│   ├── Industry Selector Dropdown (e.g., [Beauty E-Commerce ▼], [EV Automotive ▼])
│   ├── [+ New Industry Wizard] Button
│   ├── [⚡ Run Live AI Scan] Button
│   └── [Export Data] Button
│
├── 2. Asymmetric Executive Hero Composition
│   ├── Left (60%): Dominant Signal Headline (Newsreader Serif) + Big Number (76.7%) + Avg Rank + Pos Sentiment
│   └── Right (40%): Supporting Indicators Ledger (Trust Index, Citation Nodes, Lag Sync)
│
├── 3. Quiet Enterprise Navigation Rail
│   ├── 01 Market Share & Distribution
│   ├── 02 Citation Authority Network
│   ├── 03 Strategic Interventions
│   ├── 04 Scenario Planning Model
│   └── 05 Forensic Query Archive
│
├── 4. Interactive Drawers & Modals (Self-Service)
│   ├── Modal A: "+ Create New Custom Vertical & Brands"
│   ├── Modal B: "1-Click AI Scan Launcher" (Select Engine, Sample Count, Start Button)
│   └── Modal C: "Live Scan Progress & Output Stream" (0% -> 100% Progress Bar + Step logs)
│
└── 5. JavaScript Runtime
    ├── Local & REST API Data Sync
    ├── Chart.js Lifecycle Controller
    ├── Scenario Simulator Math Engine
    └── Instant Table Filter
```

---

# 5. BACKEND API CONTRACT (FASTAPI REST SERVICES)

All endpoints served by `src/api.py` on `http://localhost:8000`:

### `GET /api/v1/verticals`
* Returns array of all available industries and their brand configurations.

### `POST /api/v1/verticals`
* Creates a new vertical with custom brand entities and generated queries.
* **Payload:**
```json
{
  "vertical_id": "ev_automotive_th",
  "name_th": "ตลาดรถยนต์ไฟฟ้าไทย (EV)",
  "name_en": "Thailand EV Automotive Market",
  "focal_brand": "byd",
  "brands": [
    { "id": "byd", "name": "BYD Thailand", "aliases": ["บีวายดี", "BYD"], "is_focal": true },
    { "id": "tesla", "name": "Tesla Thailand", "aliases": ["เทสลา", "Tesla"], "is_focal": false },
    { "id": "mg", "name": "MG Thailand", "aliases": ["เอ็มจี", "MG"], "is_focal": false }
  ]
}
```

### `POST /api/v1/scan`
* Triggers background AI observation scan.
* **Payload:**
```json
{
  "vertical_id": "ecommerce_retail_th",
  "engine_type": "gemini", // "gemini" | "tavily" | "openrouter" | "mock"
  "count": 30,
  "include_control_set": true
}
```
* **Response:** `{ "task_id": "scan_20260829_001", "status": "QUEUED" }`

### `GET /api/v1/scan/{task_id}/progress`
* Server-Sent Events (SSE) stream or JSON poll returning:
  `{ "progress_pct": 65, "completed_queries": 20, "total_queries": 30, "current_query": "แคมเปญ Double Day..." }`

### `GET /api/v1/metrics/{vertical_id}`
* Returns calculated Share of Voice, Net Recommendation Score, Top Citations, and Leaderboard for the requested vertical.

### `GET /api/v1/queries/{vertical_id}`
* Returns all benchmark prompts and AI evidence rows with search metadata.

---

# 6. STEP-BY-STEP IMPLEMENTATION ROADMAP

| Phase | Milestone & Objective | Deliverables |
| :--- | :--- | :--- |
| **Phase 1** | **Universal Entities Expansion** | อัปเดต `config/entities.yaml` ให้มี 6 อุตสาหกรรมหลักของไทย พร้อมระบบ Dynamic Fallback |
| **Phase 2** | **FastAPI Backend Server** | สร้าง `src/api.py` พร้อม Endpoints สำหรับ Verticals, Scans, Metrics, และ SSE Progress |
| **Phase 3** | **Self-Service Web UI Integration** | อัปเดต `dashboard/web/index.html` ให้มี **Industry Switcher**, **Brand Wizard Modal**, และ **1-Click Scan Modal** |
| **Phase 4** | **One-Click Unified Launcher** | เพิ่มคำสั่ง `python src/cli.py serve` เพื่อรัน FastAPI + Static Web UI จบในคำสั่งเดียว |
| **Phase 5** | **Testing & CI/CD Verification** | เพิ่ม Unit Tests ใน `tests/test_api.py` ตรวจสอบสถานะ 100% Green และ Ruff Compliance |

---

# 7. MASTER PROMPT FOR AGENT / CODE GENERATION

คุณสามารถก๊อปปี้ Master Prompt ด้านล่างนี้เพื่อสั่งให้ระบบหรือ AI Agent ดำเนินการอัปเกรดทั้งระบบตามสเปกนี้ได้ทันที:

```markdown
# TASK: IMPLEMENT FULL-STACK UNIVERSAL AI MARKET INTELLIGENCE PLATFORM (V4.0)

โปรดดำเนินการอัปเกรดระบบ ai_brand_tracker สู่ Full-Stack Universal Architecture ตามเอกสาร docs/UNIVERSAL_AI_PLATFORM_V4_BLUEPRINT.md โดยมีข้อกำหนดดังนี้:

1. Backend API (FastAPI - src/api.py):
   - สร้าง REST endpoints: /api/v1/verticals, /api/v1/scan (Background Task), /api/v1/scan/{id}/progress, /api/v1/metrics/{vertical_id}, /api/v1/queries/{vertical_id}
   - เชื่อมต่อกับ QueryUniverseGenerator, EngineFactory (Gemini, Tavily, OpenRouter, Mock), และ DuckDBStore

2. Universal Verticals (config/entities.yaml):
   - บรรจุ 6 อุตสาหกรรมหลักของไทย (E-Commerce, EV Automotive, Banking FinTech, Real Estate, Hospitals, F&B Coffee)

3. Self-Service Web UI (dashboard/web/index.html):
   - รักษา Palette สไตล์ Q: #F2F0EF, #C9C8C7, #949392, #66615E, Black
   - เพิ่ม Top Bar: Industry Selector Dropdown, ปุ่ม [+ Add Industry], ปุ่ม [⚡ Run Live AI Scan]
   - เพิ่ม Modal สร้างแบรนด์ใหม่ และ Modal สั่งสแกนสดพร้อมแถบ Progress Bar 0-100%
   - กราฟและตารางทั้งหมดเปลี่ยนข้อมูลตามอุตสาหกรรมที่เลือกแบบ Real-Time

4. Unified Launcher & CLI:
   - เพิ่มคำสั่ง `python src/cli.py serve --port 8000` เพื่อรัน Backend และเปิดหน้าเว็บ Web UI อัตโนมัติ

5. Quality & Tests:
   - เพิ่ม Unit Tests ใน tests/test_api.py
   - รัน `ruff check .` (0 errors) และ `pytest tests/` (100% passing)
```

---
*เอกสารนี้คือ Single Source of Truth สำหรับการพัฒนาแพลตฟอร์มเวอร์ชัน 4.0 ต่อไป*
