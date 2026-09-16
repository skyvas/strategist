# 02: Ground Truth Software Requirements Specification (SRS)

> **Author**: Business Discovery & Requirements Analyst
> **Status**: Draft (Discovery Phase 4)
> **Project**: Import/Export Pipeline (Canada ⇄ India) - Kairi & Co. Achar

---

## 1. Core Requirements (The "Must-Haves")

The system exists solely to prevent the operational pipeline from halting due to missing documents, lack of inventory, or miscommunication across a 10.5-hour time zone difference.

- **REQ-CORE-01 (Inventory Visibility):** Partner A (Canada) and Partner H (India) must have a unified, real-time view of inventory levels across both the Canadian warehouse (CFIA cleared) and the Indian warehouse (pre-export).
- **REQ-CORE-02 (Compliance Document Verification):** The system must enforce a "hard gate" preventing shipment dispatch until a predefined set of mandatory export/import documents (Commercial Invoice, Packing List, FSSAI Certificate, Phytosanitary Certificate) are uploaded and verified.
- **REQ-CORE-03 (Automated Handoffs):** Transitions between workflow states (e.g., "Production Complete" -> "Ready for Freight") must automatically trigger notifications to the relevant downstream actor (e.g., the Freight Forwarder or Canadian Customs Broker) without manual email drafting.

---

## 2. Functional Requirements

### 2.1. Order & Demand Management
- **FR-01 (Re-order Trigger):** When Canadian B2B/D2C sales deplete a specific SKU below the 60-day moving average threshold, the system must automatically generate a "Production Request" ticket for Partner H.
- **FR-02 (B2B Invoicing):** Partner A must be able to generate compliant Canadian tax invoices (including GST/HST) for B2B grocery store wholesale orders directly from the central hub.

### 2.2. Logistics & Document Management
- **FR-03 (Document Repository):** The system must provide a structured upload portal attached to specific "Shipment IDs" rather than relying on disparate email threads.
- **FR-04 (Customs Broker Portal):** The system must provide a read-only, secure access link for the Canadian Customs Broker to download required clearance documents instantly.
- **FR-05 (Status Tracking):** The system must track the state of the shipment: *In Production, QA Passed, At Port (India), In Transit (Ocean), Customs Clearance (Canada), Warehoused (Canada).*

---

## 3. Non-Functional Requirements

- **NFR-01 (Low Friction / No-Code Preference):** Neither Partner H nor Partner A has dedicated IT staff. The solution should leverage existing, robust SaaS platforms (e.g., Airtable, Notion, Shopify, Zapier) rather than custom-built web applications that require ongoing maintenance.
- **NFR-02 (Mobile Accessibility):** Partner H will primarily manage operations from the factory floor in India. The system's primary interface for Partner H must be fully functional on a mobile device (e.g., uploading photos of QA drop-tests via a mobile form).
- **NFR-03 (Asynchronous Communication):** The system must assume that when Partner A updates a status, Partner H is asleep. Alerts must be clearly queued and categorized (Urgent vs. Routine) upon waking.
- **NFR-04 (Auditability):** Every state change in the pipeline (e.g., who approved the QA check, when the customs broker downloaded the invoice) must be timestamped and logged to resolve disputes (Rework/NVA-R) quickly.
