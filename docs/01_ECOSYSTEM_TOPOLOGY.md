# 01: Ecosystem Topology

> **Author**: Business Discovery & Requirements Analyst
> **Status**: Draft (Discovery Phase 3)
> **Project**: Import/Export Pipeline (India to Canada) - Kairi & Co. Achar

---

## 1. High-Level Architecture & Supply Chain Flow

The Kairi & Co. ecosystem requires a lean, low-overhead supply chain bridging Indian sourcing with Canadian B2B/B2C distribution. The pipeline consists of three core domains:

1. **Origin Domain (India):** Sourcing, production, QA, and export compliance. Managed by **Partner 'H'**.
2. **Destination Domain (Canada):** Import compliance, warehousing, B2B grocery sales, and Shopify D2C fulfillment. Managed by **Partner 'A'**.
3. **Orchestration Layer (System/AI):** A central nervous system (e.g., automated WhatsApp/Email alerts, headless ERP, or basic Airtable/Notion tracker) to minimize "Wait Time (NVA-W)" between H and A.

### Pipeline Flow:
`Raw Material Sourcing (H) -> Production & Bottling (H) -> FSSAI/Export QA (H) -> Freight Forwarding (H/A) -> CFIA/Customs Clearance (A) -> Warehousing/3PL (A) -> B2B/B2C Fulfillment (A)`

---

## 2. Component Boundaries & Actor Delegation

To avoid time-zone fatigue and rework (NVA-R), boundaries must be strict and asynchronous.

### Actor 1: Partner 'H' (India - Origin Operations)
* **Core Value-Add (VA):** Securing the best raw materials, managing the manufacturer, ensuring authentic flavor profiles.
* **Responsibilities:**
  - **Sourcing & Production:** Vendor management, contract manufacturing oversight.
  - **Quality Assurance:** Ensuring the product matches the *Kairi & Co.* standard (no leaking jars, proper labeling, correct spice levels).
  - **Export Compliance:** Handling APEDA, FSSAI, and obtaining necessary Phytosanitary certificates or Certificates of Origin.
  - **Logistics (Origin):** Delivering the product to the Indian port/freight forwarder.

### Actor 2: Partner 'A' (Canada - Destination Operations & Sales)
* **Core Value-Add (VA):** Selling the product, managing Canadian logistics, and driving revenue.
* **Responsibilities:**
  - **Import Compliance:** Ensuring all CFIA (Canadian Food Inspection Agency) and SFC (Safe Food for Canadians) regulations are met. Managing the Customs Broker.
  - **B2B Grocery Sales:** Pitching the product to Indian/South Asian grocery stores in Canada.
  - **D2C E-commerce:** Managing the Shopify website, marketing, and order fulfillment (or 3PL management).
  - **Demand Planning:** Forecasting inventory needs and signaling Partner 'H' for re-orders before stockouts occur.

### Actor 3: System / AI Orchestrator (The "Anti-Fatigue" Layer)
* **Core Value-Add (VA):** Eliminating the wait time (NVA-W) caused by the 10.5-hour time difference.
* **Responsibilities:**
  - **Document Handoff:** Automated validation that Partner H has uploaded the correct Commercial Invoice, Packing List, and Certificates before the shipment leaves India, instantly notifying Partner A's broker.
  - **Inventory Triggers:** Automated alerts to Partner H when Canadian inventory hits a re-order threshold.

---

## 3. Interfaces & Integrations (Minimal Viable Tech Stack)

Do not over-engineer. The goal is to sell achar, not build a software company.

1. **Information Hub:** Notion or Airtable.
   - *Use:* Single source of truth for inventory, shipment tracking, and document storage. Eliminates "Can you email me that form again?" (Rework).
2. **Communication:** WhatsApp Business + Automated Email Routing.
   - *Use:* Asynchronous updates. Urgent alerts trigger specific channels.
3. **Commerce:** Shopify (D2C) + Simple B2B invoicing (e.g., Quickbooks or Shopify B2B).
   - *Use:* Handles all Canadian sales, inventory tracking, and payment processing.
4. **Customs Interface:** Managed via a licensed Customs Broker (outsourced).
   - *Use:* Do not build software for customs. Handoff the required PDFs via a shared Google Drive/Airtable portal.

---

## 4. Identified Bottlenecks & Operational Liabilities

1. **The Customs Handoff (High Risk of Wait Time - NVA-W):** If Partner H ships the goods but Partner A's broker lacks the correct paperwork, the shipment sits at the port accumulating demurrage fees. 
   - *Solution:* Hard gate. Goods cannot leave the Indian warehouse until the broker in Canada confirms receipt of the digital paperwork.
2. **Production Lead Time vs. Ocean Freight:** Sea freight takes 30-45 days. 
   - *Solution:* Partner A must establish a strict inventory par level on Shopify/Airtable that triggers a re-order signal to Partner H at least 60 days before a stockout.
3. **Quality Control Rework (NVA-R):** If jars leak during transit, the product is dead on arrival.
   - *Solution:* Partner H must implement a drop-test and pressure-test standard operating procedure (SOP) before palletization.
