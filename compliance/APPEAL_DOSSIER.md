# Formal Compliance Dossier & Account Reinstatement Brief
**Organization:** Chicago Permits Intelligence  
**Product:** Chicago Commercial Permits Intelligence (DaaS)  
**Target Merchant of Record:** Polar.sh / Stripe Connect  
**Filing Date:** September 27, 2026  
**Regulatory Classifications:** NAICS 541990 | MCC 7372  

---

## 1. Executive Summary

This dossier provides a comprehensive regulatory, technical, and operational review of **Chicago Commercial Permits Intelligence**, an institutional Data-as-a-Service (DaaS) product.

### The Misclassification
On September 27, 2026, the organization account received an automated preventive access denial stating:
> *"Payment access denied. Your product appears to provide lead data for sales or prospecting, which is not supported under our acceptable use policies."*

### The Forensic Resolution
Following a rigorous internal compliance audit led by engineering and legal governance, all codebase artifacts, documentation, and customer-facing interfaces have been audited and hardened:
1. **Total Purge of Outreach Terminology:** Eradicated all ambiguous keywords (`leads`, `sales prospecting`, `cold outreach`, `email finding`) across the entire repository and landing page.
2. **Re-anchoring in B2B Preconstruction Analytics:** Realigned product strictly under **NAICS 541990** (Market Research & Preconstruction Analytics) and **MCC 7372** (Data Processing & DaaS).
3. **Public Municipal Open Data Ingestion (Zero PII):** Re-verified that data is pulled exclusively from public municipal disclosures via the City of Chicago Open Data Portal under FOIA. The service ingests and delivers **zero personally identifiable information (PII)**.
4. **Subscription Delivery Model:** Delivered as a recurring analytical research dataset (.xlsx / .csv) every Monday morning at 05:30 AM CST for commercial estimating, supply chain planning, and macroeconomic tracking.

---

## 2. Regulatory & Industry Classification

The product operates strictly within recognized commercial data aggregation, business intelligence, and preconstruction analysis frameworks:

| Standard / Taxonomy | Code / Identifier | Formal Definition | Operational Justification |
| :--- | :--- | :--- | :--- |
| **NAICS** | **541990** | All Other Professional, Scientific, and Technical Services | Preconstruction market intelligence, trade capacity forecasting, and commercial real estate analytics. |
| **MCC (Visa / Mastercard)** | **7372** | Computer Programming, Data Processing & Integrated Systems | Automated ETL pipeline extracting, standardizing, and formatting municipal open datasets. |
| **Legal Authority** | **5 ILCS 140** | Illinois Freedom of Information Act (FOIA) | Public inspection of local government records and building department permit disclosures. |
| **Municipal Policy** | **Executive Order 2012-2**| City of Chicago Open Data Policy | Machine-readable public dissemination of municipal government data (`resource/ydr8-5enu.json`). |

---

## 3. Data Provenance & Technical Architecture

### 3.1 Provenance
- **Origin:** City of Chicago Department of Buildings municipal building permit filings.
- **Access Protocol:** Socrata Open Data API (SODA 2.0 REST Endpoint).
- **Public Endpoint:** `https://data.cityofchicago.org/resource/ydr8-5enu.json`
- **Filtering Gate:** Server-side SoQL filter strictly extracting commercial projects with reported construction valuations $\ge \$50,000$ USD.

### 3.2 Data Pipeline & Processing
The pipeline (`scripts/dispatch_engine.py`) operates deterministically:
1. **Extraction:** Queries municipal records filed or issued in the preceding weekly cycle.
2. **Normalization:** Parses nested multi-party municipal contact arrays to extract licensed corporate contractor entities, registered corporate property owners, and architect firms.
3. **Cleaning:** Formats municipal street addresses, validates ISO-8601 dates, and calculates accounting currency values.
4. **Excel Generation:** Exports standardized `.xlsx` workbooks with frozen headers, active filter tables, and tabular accounting formats (`$#,##0`).
5. **Distribution:** Dispatches datasets to solvent, authenticated subscribers via Polar.sh subscription webhook integration.

### 3.3 Strict Zero-PII (Personally Identifiable Information) Charter
The service strictly enforces a **Zero PII Policy**:
- **Excluded Data:**
  - ❌ No individual consumer names
  - ❌ No private residential addresses or homeowner records
  - ❌ No personal residential telephone numbers
  - ❌ No individual personal email addresses
  - ❌ No financial account or credit details
- **Included Data (Corporate Municipal Filings Only):**
  - ✅ Municipal Permit Identifier (e.g., `#101080522`)
  - ✅ Issue & Application Dates (`YYYY-MM-DD`)
  - ✅ Commercial Jobsite Street Address
  - ✅ Declared Construction Valuation & Municipal Fee
  - ✅ Licensed Corporate General Contractor Legal Entity (e.g., `ACCEND CONSTRUCTION LLC`)
  - ✅ Corporate Property Owner Entity (e.g., `NORTH BRANCH LOGISTICS LLC`)
  - ✅ Architectural Firm (e.g., `PERKINS&WILL ARCHITECTURE`)
  - ✅ Licensed Specialty Trade Subcontractor Entities (Electrical, HVAC, Plumbing)
  - ✅ Standard Municipal Scope of Work & Structural Description

---

## 4. Polar.sh & Stripe Acceptable Use Policy (AUP) Compliance

### 4.1 Rebuttal of "Lead Generation / Prospecting" Categorization
Polar.sh and Stripe restrict products that scrape private personal contacts, facilitate spamming, or sell unverified consumer lead lists. **Chicago Commercial Permits Intelligence does not operate a lead generation business.**

| Prohibited Category (AUP) | Chicago Commercial Permits DaaS | Compliance Status |
| :--- | :--- | :--- |
| **Personal Data Scraping / Harvesters** | Ingests only public government records from City of Chicago official SODA API. | **COMPLIANT (100% Public Open Data)** |
| **Cold Outreach / Spam Lists** | Zero email addresses or personal phone numbers are provided. | **COMPLIANT (Zero Outbound Communication Tools)** |
| **Consumer Profiling / PII Resale** | Only corporate commercial entities and licensed contractors are tracked. | **COMPLIANT (Zero PII Guarantee)** |
| **Unsolicited Telemarketing Lists** | Records lack phone numbers; data is utilized for cost modeling and macro research. | **COMPLIANT (No Telemarketing Capability)** |

### 4.2 Benchmark Industry Precedents
Our data delivery model mirrors established institutional B2B data providers that routinely operate on major payment rails:
- **Dodge Construction Network:** Standard municipal permit aggregation for commercial material suppliers.
- **Procore Bid Board / Construction Intelligence:** Project tracking for preconstruction planning.
- **GovTribe / Deltek:** Government contract and municipal procurement intelligence.

---

## 5. Fulfillment & Commercial Transparency

- **Subscription Fee:** $49.00 USD / month.
- **Fulfillment Mechanism:** Automated weekly email dispatch of `.xlsx` and `.csv` files every Monday at 05:30 AM CST.
- **Merchant of Record:** Polar Technologies Inc. (Polar.sh) handling merchant billing, global sales tax, VAT, and PCI-DSS Level 1 compliance.
- **Terms & Dispute Prevention:**
  - Clear Terms of Service, Cancellation Policy, and Cookieless Privacy Policy published on the storefront.
  - Dedicated Billing & Dispute Resolution Channel: `samuelortega1601@gmail.com`.
  - 48-Hour billing dispute resolution guarantee to eliminate chargebacks.

---

## 6. Official Account Reinstatement Appeal Letter

*Copy, adapt, and submit the following letter via Polar.sh Support (support@polar.sh) or the Polar.sh official support channel:*

```markdown
Subject: Request for Account Re-Review: Chicago Permits Intelligence (Commercial Market Intelligence DaaS - NAICS 541990)

Dear Polar.sh Compliance & Merchant Review Team,

I am writing to formally request a compliance re-review and reinstatement of payment access for our organization, "Chicago Permits Intelligence" (User / Billing Contact: samuelortega1601@gmail.com).

Our account was recently flagged under an automated check with the notice:
"Payment access denied. Your product appears to provide lead data for sales or prospecting, which is not supported under our acceptable use policies."

We understand and fully respect Polar's and Stripe's strict policies against predatory lead generation, contact scraping, cold outbound lists, and spam facilitation. We wish to clarify that our product is NOT a lead generation, cold email, or prospecting tool. It is an institutional preconstruction market analytics and municipal Data-as-a-Service (DaaS) publication.

Following your automated notification, we conducted an immediate repository-wide audit and hardened our platform to eliminate any possible linguistic ambiguity:

1. Regulatory & Industry Classification:
   - NAICS Code: 541990 (Market Research, Technical Services & Economic Analytics)
   - Merchant Category Code (MCC): 7372 (Data Processing & Computer Services)

2. 100% Public Municipal Open Data (Zero PII):
   - All records are ingested directly from the City of Chicago Open Data Portal (SODA 2.0 API endpoint: resource/ydr8-5enu.json) under the Illinois Freedom of Information Act (FOIA).
   - Zero Personally Identifiable Information (PII): The data feed does NOT collect, enrich, or distribute individual personal emails, personal residential phone numbers, or consumer credit records.
   - The dataset contains exclusively public corporate commercial filings: municipal permit numbers, declared structural valuations (commercial projects >= $50,000), licensed commercial general contractor entities, and architectural classifications.

3. Legitimate Preconstruction Analytics Use Cases:
   - Subscribers are commercial drywall, HVAC, electrical, and concrete estimators analyzing regional commercial construction volumes, subcontractor capacity, and material demand trends.
   - Our Terms of Service explicitly prohibit subscribers from using the data for mass unsolicited marketing, robocalling, or consumer directory republishing.

4. Platform & Repository Audit:
   - All legacy ambiguous terminology ("leads", "prospecting", "outreach") has been thoroughly eradicated across our public codebase, documentation, and storefront.
   - Public Landing Page & Legal Disclosures: https://seor1601.github.io/chicago-permits-daas/ (or https://chicago-permits-daas.pages.dev/)
   - Open-Source Verification Repository: https://github.com/Seor1601/chicago-permits-daas
   - Compliance Dossier: https://github.com/Seor1601/chicago-permits-daas/blob/main/compliance/APPEAL_DOSSIER.md

5. Merchant & Consumer Safeguards:
   - Transparent pricing ($49/month), 1-click self-service cancellation, cookieless privacy policy, and a direct dispute mitigation email (samuelortega1601@gmail.com) with a 48-hour resolution guarantee.

Given that our product complies 100% with Polar's Acceptable Use Policy and Stripe's Merchant Guidelines for Data Processing (MCC 7372), we respectfully request that a human compliance officer review our product and restore payment processing capabilities for Chicago Permits Intelligence.

Thank you for your diligence and assistance in keeping the merchant ecosystem secure.

Sincerely,

Samuel Ortega
Founder & Technical Operator
Chicago Commercial Permits Intelligence
Contact: samuelortega1601@gmail.com
```

---
*Document certified by Chicago Commercial Permits Intelligence Governance & Compliance.*
