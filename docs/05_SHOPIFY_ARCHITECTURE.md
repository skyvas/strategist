# 05: Shopify Architecture & D2C Strategy

> **Status**: In Development
> **Project**: Kairi & Co. Achar

---

## 1. UI/UX Design System & Mockups

Before writing code, we established the visual design system to ensure the Shopify storefront feels premium, modern, and distinctively Indian.

**Design Tokens:**
- **Primary Background:** Soft Cream (`#FDFBF7`)
- **Text (Headings):** Deep Charcoal (`#1A1A1A`) using *Editorial New* or a similar elegant serif.
- **Text (Body):** *Inter* or *Roobert* for clean legibility.
- **Accent/Action Color:** Marigold Orange (`#E59E2B`) and Rani Pink (`#E03178`).

---

## 2. Theme Selection & Liquid Architecture

We will build on top of a premium Shopify OS 2.0 Theme (Recommendation: **Dawn** customized, or **Focal**) to maintain high performance while enabling rich visual storytelling.

### Core Templates
- `index.json` (Homepage): Focuses on the "Hero" visual, a distinct split between "The Heritage Collection" and "The Studio Collection", and a shoppable Instagram grid.
- `product.json` (PDP): Optimized for fast mobile checkout. Features a sticky "Add to Cart" bar on scroll, spice-level indicator, and an accordion for Ingredients, Nutritional Info, and Pairings.
- `collection.json`: Clean grid layouts with robust sidebar filtering (by spice level, dietary needs, flavor profile).

---

## 3. The "Frictionless Checkout" App Stack

To minimize apps (which slow down the site) we only install what drives conversion and operational efficiency:

1. **Slide-Out Cart (e.g., UpCart or custom Liquid):**
   - Must include a "Free Shipping Progress Bar" (e.g., "Add $12 to get Free Shipping").
   - 1-click in-cart upsells (e.g., "Add a Tasting Spoon for $5").
2. **Accelerated Checkout Options:**
   - Native Shopify integration for Apple Pay, Google Pay, and Shop Pay placed directly in the slide-out cart.
3. **Reviews Engine (Okendo / Loox):**
   - Critical for food products. We need photo and video review capabilities showing how customers use the achar.
4. **Subscription Management (Skio or Recharge):**
   - Condiments have high repeat purchase rates. Enable a "Subscribe & Save 15%" option on every PDP.

---

## 4. Product Catalog & Data Model (Metafields)

To power the rich UI on the Product Pages without hardcoding, we will use Shopify Metafields attached to every product.

**Required Product Metafields (Namespace: `custom`):**
- `spice_level` (Type: Integer 1-5, renders as flame icons 🔥)
- `flavor_profile` (Type: Single line text, e.g., "Tart, Mustardy, Fiery")
- `perfect_pairings` (Type: List of single line texts, e.g., ["Avocado Toast", "Samosas", "Grilled Cheese"])
- `ingredients_list` (Type: Multi-line text)
- `is_fusion` (Type: Boolean, to easily filter Heritage vs Studio collections)

### Product Strategy: The "Build Your Own Box"
Instead of forcing customers to buy 1 jar, we push a 3-pack "Tasting Box" to increase Average Order Value (AOV) and absorb shipping costs. This will be built using Shopify's native Bundles app or a simple custom Liquid form passing multiple variant IDs to the cart.
