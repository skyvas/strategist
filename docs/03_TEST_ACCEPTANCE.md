# 03: Test & Acceptance Criteria

> **Author**: Business Discovery & Requirements Analyst / QA Adversary
> **Status**: Draft (Discovery Phase 4)
> **Project**: Import/Export Pipeline (Canada ⇄ India) - Kairi & Co. Achar

---

## 1. Definition of Done (DoD)

The operational pipeline and supporting system are considered "Done" when:
1. Partner H can successfully log a production batch, upload all compliance documents (Commercial Invoice, Packing List, FSSAI), and signal that the goods are ready for freight from a mobile device in India.
2. The system automatically blocks the "Shipped" status if mandatory documents are missing.
3. The Canadian Customs Broker can access the required documents without needing an email from Partner A.
4. Partner A receives stock into the Canadian system, and sales correctly decrement the unified inventory count.
5. The system automatically alerts Partner H when a SKU falls below the defined 60-day threshold.

---

## 2. Unit & Integration Testing Scenarios

These tests validate specific components of the No-Code/System architecture:

- **Test-01 (Document Upload Validation):**
  - *Action:* Partner H attempts to mark a shipment as "Ready for Export" without uploading the Phytosanitary Certificate.
  - *Expected Result:* The system rejects the state change and highlights the missing required field.
- **Test-02 (Mobile Responsiveness):**
  - *Action:* Partner H uploads a photo of a leak-test via their mobile phone on 4G network.
  - *Expected Result:* The image uploads successfully, attaches to the correct Shipment ID, and is immediately visible to Partner A.
- **Test-03 (Inventory Decrement - Shopify Sync):**
  - *Action:* A mock order for 3 jars of "The Classic Kairi" is placed on the Shopify D2C site.
  - *Expected Result:* The central inventory hub (Airtable/Notion) reflects a reduction of 3 units within 5 minutes.

---

## 3. End-to-End (E2E) Acceptance Tests (Dry Run)

Before risking capital on a live ocean freight shipment, the partners must execute a "Dry Run" using dummy data.

- **E2E-01: The Perfect Flow (Happy Path)**
  1. Partner H creates Shipment #001 (Dummy 500 units).
  2. Partner H uploads dummy PDFs for all export documents.
  3. System notifies Canadian Broker (simulated by a test email).
  4. Partner H marks shipment "In Transit".
  5. Partner A marks shipment "Cleared Customs" and "Received in Warehouse".
  6. Inventory instantly shows 500 available units in Canada.
  - *Acceptance:* Zero emails were sent manually between H and A during this process.

- **E2E-02: The Stockout Alert (Edge Case)**
  1. System inventory is manually set to 100 units (representing a 50-day supply, assuming a 60-day threshold).
  2. *Acceptance:* Within 1 hour, Partner H receives an automated WhatsApp or High-Priority Email notifying them that Production Request #002 needs to be initiated immediately.

- **E2E-03: The Leaky Jar (QA Failure / Rework)**
  1. During the Indian warehouse QA phase, Partner H marks 50 jars as "Failed QA - Leaking".
  2. *Acceptance:* The total export quantity is automatically updated on the Commercial Invoice and Packing list before it is sent to the broker, ensuring customs documents match the actual physical shipment perfectly.
