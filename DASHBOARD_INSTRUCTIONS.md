---
methodology_version: 0.4.0
last_updated: 2026-06-04
status: living methodology
project: Billionaire Papers and Physical Intelligence
dashboard_narrative: billionaire_papers_to_physical_intelligence_to_value_capture
---

# Billionaire Papers and Physical Intelligence Dashboard Instructions

## Purpose

Build a reproducible, standalone HTML dashboard and Google Colab notebook that use the billionaire-papers dataset to support and stress-test this thesis:

> Physical Intelligence / Physical AI is a plausible next major AI wave for science because the historical billionaire-paper base already created the platforms needed for AI systems to perceive, simulate, plan, manipulate, manufacture, synthesize, test, measure, and learn from the physical world.

This is a thesis, not a certainty. The dashboard must present evidence, uncertainty, and failure modes alongside the argument.

## Core Narrative

The dashboard should lead viewers through this transition:

```text
Billionaire papers
    ↓
Enabling scientific / technical platforms
    ↓
AI models + robotics + simulation + automated labs
    ↓
Physical Intelligence companies
    ↓
Science acceleration in biology, chemistry, materials, robotics,
aerospace, energy, agriculture, and manufacturing
    ↓
Country-level value capture and strategic advantage
```

The first billionaire-paper wave created scientific and technological platforms including batteries, semiconductors, solar, robotics, computer vision, transformers, AI for biology, cloud infrastructure, molecular biology, automation, and materials science.

The generative-AI wave converted knowledge into language, images, code, predictions, and reusable model interfaces.

The next wave under test is Physical Intelligence: AI connected to sensors, instruments, robots, factories, labs, supply chains, physical simulation, and experimental feedback loops.

## Required Audience Modes

### Story Mode

Story Mode is for non-experts, investors, policymakers, and first-time viewers. It should:

1. Explain the thesis in a guided sequence.
2. Show the platform base created by the billionaire papers.
3. Explain how generative AI bridges knowledge and prediction.
4. Show the Physical Intelligence capability stack.
5. Identify science and physical-industry domains that may accelerate.
6. Connect the thesis to US, EU, and China value-capture roles.
7. Include caveats so the presentation does not become hype.

### Data Explorer

Data Explorer is for researchers, analysts, and data engineers. It should use two tabs:

1. `Papers`: the billionaire-paper table with filters for confidence tier, broad area, research-origin country, and public/private origin.
2. `Companies`: the active Physical AI company table with filters for strategic region, country, sub-field, active status, investment evidence confidence, and funding caution.
3. A shared search box should search the active tab across paper titles, authors, institutions, company names, countries, fields, rationales, Physical AI use cases, investment notes, and source links.
4. Origin-country analysis, China/US/EU beneficiary-role views, downloadable CSV outputs, and Colab reproducibility details should remain available elsewhere in the dashboard.

## Required Input Priority

| File | Purpose | Required |
|---|---|---|
| `billionaire_papers_1976_2026_china_benefit_updated.csv` | Preferred source file with China beneficiary fields. | Preferred |
| `billionaire_papers_1976_2026.csv` | Fallback source paper list. | Yes if preferred file is absent |
| `paper_country_benefit_china_update_long.csv` | China-specific partial value-capture assumptions. | No |
| `physical_ai_companies_active_updated_investments.csv` | Active-only Physical AI / Physical Intelligence company landscape with investment estimates. | No, required for company landscape charts |
| `paper_benefit_assumptions_template.csv` | Editable country value-capture assumptions; regenerated as needed. | No |

## Required Outputs

| File | Purpose |
|---|---|
| `billionaire_papers_dashboard.ipynb` | Google Colab notebook with the full reproducible workflow. |
| `billionaire_papers_dashboard.html` | Standalone interactive HTML dashboard with Story Mode, Physical Intelligence thesis, country capture, Dataset Explorer, and downloads. |
| `DASHBOARD_INSTRUCTIONS.md` | Living methodology and design guide. |
| `physical_intelligence_thesis_links.csv` | Rule-based paper → platform family → Physical Intelligence capability → science-domain links. |
| `physical_intelligence_domain_summary.csv` | Domain-level summary for the thesis layer. |
| `physical_ai_companies_active_clean.csv` | Cleaned active company table with sub-field, country, region, and investment fields. |
| `physical_ai_company_country_summary.csv` | Active company-country exposure counts and fractional funding view. |
| `physical_ai_company_subfield_summary.csv` | Active company counts and funding estimates by Physical AI sub-field. |
| `physical_ai_company_region_summary.csv` | Strategic-region comparison table for company counts and investment estimates. |
| `paper_benefit_assumptions_template.csv` | Editable country-benefit assumptions table. |
| `paper_country_benefit_estimates.csv` | Role-level low/base/high value-capture and profit-proxy estimates. |
| `paper_country_benefit_long.csv` | Long-form value-capture table. |
| `paper_country_benefit_china_update_long.csv` | China-specific partial benefit table, if available. |
| `country_summary.csv` | Aggregated beneficiary-country summary. |
| `china_value_capture_summary.csv` | Compact summary of China capture-share assumptions. |
| `origin_country_summary.csv` | Aggregated research-origin summary. |
| `origin_to_beneficiary_flow.csv` | Origin → platform → beneficiary/role flow table. |
| `field_country_summary.csv` | Beneficiary-country totals by field/platform. |
| `public_private_spillover_summary.csv` | Value capture grouped by public/private/mixed origin. |
| `quality_check_report.csv` | Machine-readable data-quality and model-readiness warnings. |
| `requirements.txt` | Colab-friendly Python package list. |

## Physical Intelligence Thesis Layer

The Physical Intelligence layer is derived from the source paper table. It is not a new source of truth.

| Derived field | Meaning |
|---|---|
| `pi_platform_family` | Broad platform family such as AI models, robotics, cloud/data, molecular biology, batteries, solar, semiconductors, materials, or agricultural biotechnology. |
| `pi_capability` | Capability such as perceive/measure, predict/model/generate, plan/control, manipulate/manufacture, synthesize/test, learn from physical-world data, or secure/coordinate infrastructure. |
| `science_acceleration_domain` | Candidate domain affected by the platform: biology and health, chemistry and materials, robotics and automation, aerospace and mobility, energy and climate, agriculture, manufacturing, digital infrastructure, or cross-domain infrastructure. |
| `pi_relevance` | Direct physical-intelligence substrate, enabling digital infrastructure, or adjacent economic platform. |
| `classification_basis` | Plain-language note that the mapping is rule-based and auditable. |

Rules for this layer:

1. Do not claim the taxonomy is definitive.
2. Show counts as paper-linked evidence, not market forecasts.
3. Keep adjacent platforms visible but label them separately from direct Physical Intelligence substrates.
4. Let users download the thesis-link CSV so classifications can be corrected over time.

## Active Physical AI Company Landscape

Use `physical_ai_companies_active_updated_investments.csv` to show the active company ecosystem connected to the thesis.

Required views:

1. Active Physical AI / Physical Intelligence companies per country.
2. Active companies by sub-field.
3. Estimated funding by sub-field.
4. Strategic-region comparison across US, EU / Europe, China / Asia, Canada, Latin America, and Other / mixed.

Aggregation rules:

1. The source file is treated as active-only, but rows are still filtered to `Active_Status` values containing `Active` and excluding `Inactive` if future files add inactive rows.
2. Mixed-country rows are counted in each listed country in the country-exposure chart.
3. Cross-region rows are bucketed as `Other / mixed` in the strategic-region comparison unless all listed countries are in the same region.
4. Funding uses `Updated_Investment_USD_M_base` as the base estimate, with low/high fields shown as uncertainty bands where available.
5. Funding estimates mix total funding, latest rounds, IPO/public-market proceeds, acquisition consideration, and range-based estimates. They are directional strategy signals, not audited capital accounts.

## Required Story Charts

### 1. Physical Intelligence Capability Chart

Show paper-linked capabilities such as perception, prediction, control, manufacturing, synthesis/testing, and physical-data learning.

Requirements:

- Separate direct Physical Intelligence substrates from enabling digital infrastructure and adjacent economic platforms.
- Use labels and legend text; do not rely only on color.
- Make the chart interpretable without reading the CSV.

### 2. Platform → Capability → Domain Sankey

Show how platform families flow into Physical Intelligence capabilities and then into science/industry acceleration domains.

Requirements:

- Use the rule-based thesis-link table.
- Label it as an auditable interpretation, not a causal proof.
- Keep hover data useful and avoid tiny unreadable chart layouts.

### 3. Science Acceleration Domain Chart

Show linked paper counts for biology, chemistry, materials, robotics, aerospace, energy, agriculture, manufacturing, digital infrastructure, and cross-domain science infrastructure.

Requirements:

- Explain that links can be multi-domain and therefore should not be read as exclusive shares.
- Keep labels visible.

### 4. Active Physical AI Company Landscape Charts

Show the active Physical AI / Physical Intelligence company base.

Requirements:

- Use `physical_ai_companies_active_updated_investments.csv`.
- Show active company-country exposure counts.
- Show active company counts by sub-field.
- Show low/base/high investment estimates by sub-field.
- Compare company counts and base investment estimates across US, EU / Europe, China / Asia, Canada, Latin America, and Other / mixed.
- State that investment totals are directional and can mix funding metrics.

### 5. Total Revenue Captured Panel

Show how much total revenue the United States, European Union, and China captured only when audited dollar denominators are populated.

Requirements:

- Use `enabled market revenue x paper attribution factor x normalized country capture share`.
- Show `Not estimated yet` when denominators are missing.
- Clearly distinguish role/share coverage from revenue totals.
- Aggregate EU member-state rows into one EU total.

### 6. Public / Private / Mixed Research-Origin Chart

Show whether papers originated in public institutions, private institutions, mixed collaborations, or non-institutional settings.

Requirements:

- Use `Public_or_private` / `public_private_clean`.
- Show labels, paper counts, and percentages.
- Use public = blue, private = violet, mixed = teal.

### 7. Origin → Platform → Role Sankeys

Keep the China, US, and EU Sankeys:

- Origin → platform → China role.
- Origin → platform → US role.
- Origin → platform → EU role.

Label China as a partial beneficiary layer and US/EU as modeled assumptions.

### 8. China Origin-vs-Benefit Comparison Panel

Directly explain why China looks undercounted in origin-only views.

Requirements:

- Compare China-origin paper count with China-beneficiary paper count.
- Use large labeled counts, not a small chart.
- Include a visibility-shift multiplier and concise interpretation.

## Economic Value-Capture Methodology

Research origin is not the same as economic capture. A publication can originate in one country while commercialization, manufacturing, IP ownership, standards adoption, cloud compute, deployment, or end-market value occurs elsewhere.

The core revenue formula is:

`country_revenue_capture = enabled_market_revenue * paper_attribution_factor * normalized_country_capture_share`

The profit proxy formula is:

`country_profit_proxy = country_revenue_capture * role_margin`

Use low/base/high ranges instead of point estimates. Do not invent monetary estimates when enabled-market revenue or attribution factors are blank.

## Country Role Definitions

| Role | Definition |
|---|---|
| `research_origin` | Country where the enabling research was performed. |
| `ip_owner` | Country of major patent assignees or IP owners. |
| `licensing` | Country receiving licensing income or controlling key rights. |
| `commercialization` | Country where products were developed, scaled, or launched. |
| `company_headquarters` | Headquarters country of firms capturing revenue or profit. |
| `manufacturing` | Country where products or key components are manufactured. |
| `supply_chain` | Country supplying important upstream materials or components. |
| `equipment_supplier` | Country supplying capital equipment or tooling. |
| `cloud_compute` | Country capturing compute infrastructure or cloud-service revenue. |
| `standards_ecosystem` | Country capturing value through standard-compliant ecosystems. |
| `adoption_market` | Country receiving market, user, patient, or customer value. |
| `health_system_savings` | Country receiving avoided healthcare cost or public-health value. |
| `agricultural_yield_gain` | Country receiving farm productivity or yield gains. |
| `consumer_surplus` | Country receiving consumer value beyond price paid. |
| `strategic_capability` | Country receiving strategic capability value not captured by revenue alone. |

## Stress Tests And Caveats

The Physical Intelligence thesis is weaker when:

1. Robotics and lab automation remain too brittle for broad deployment.
2. Physical-world data are too expensive, sparse, proprietary, or noisy.
3. Simulation-to-real transfer fails in important domains.
4. Capex, regulation, safety validation, and procurement cycles slow adoption.
5. Revenue capture concentrates in incumbents rather than new science-acceleration companies.
6. Country-level role assumptions lack audited monetary evidence.
7. The dataset omits important papers, non-paper know-how, patents, process innovations, or tacit manufacturing capability.

## Visual Design System

| Meaning | Color guidance |
|---|---|
| Research origin | Blue |
| Value capture | Gold / orange |
| China highlight | Red |
| Public origin | Blue |
| Private origin | Violet |
| Mixed origin | Teal |
| Warnings | Amber |
| Success / validated | Green |
| Uncertain assumptions | Low-opacity amber bands |

Use semantic colors consistently. Do not use color as the only meaning channel.

## Accessibility Requirements

1. Strong contrast: at least 4.5:1 for normal text and 3:1 for large text where practical.
2. Visible keyboard focus states for links, buttons, inputs, and select controls.
3. No color-only meaning: pair color with labels, text, marker shape, or annotations.
4. ARIA labels for navigation, mode sections, filters, and major chart regions.
5. Chart summaries before or near important interactive charts.
6. Reduced-motion support using `prefers-reduced-motion`.
7. Responsive layout that works on mobile and desktop.
8. Plain-language warnings for partial and uncertain estimates.
9. Tables should have clear headers and should not be the only way to understand the story.

## How To Run In Google Colab

1. Upload `billionaire_papers_dashboard.ipynb` to Google Colab.
2. Upload the source CSV files when prompted, or place them in `/content/`.
3. Run all cells from top to bottom.
4. Download the generated HTML, CSVs, Markdown file, and requirements file from the Colab file browser.

## How To Improve The Dataset

Keep `ID` stable. Add new rows with unique IDs, complete DOI/link evidence where possible, and concise rationale text. For multiple origin countries, separate countries with semicolons.

For the thesis layer, review `physical_intelligence_thesis_links.csv` and correct classifications that overstate or understate Physical Intelligence relevance.

For country capture, add one row per paper, beneficiary country, and beneficiary role in the assumptions template. Fill low/base/high enabled revenue, attribution, capture share, and role margin only when there is cited evidence or a documented model assumption.

## Source And Evidence Standard

Prefer annual reports, SEC filings, investor presentations, official market reports, OECD TiVA, UN Comtrade, World Bank, IMF, WTO, OECD, WIPO, USPTO, EPO, national statistics agencies, peer-reviewed papers, Nobel materials, university technology-transfer reports, institutional histories, and patent databases.

Every high-impact monetary row should have at least one source and ideally multiple independent sources.

## Roadmap for future improvements

| Priority | Improvement | Notes |
|---|---|---|
| High | Audit the Physical Intelligence taxonomy against domain experts. | Start with AI models, robotics, automated labs, materials, biology, energy, and semiconductor rows. |
| High | Add audited market revenue and country role sources for the case-study papers. | Start with lithium-ion batteries, mRNA vaccines, PCR, transformers, CRISPR, and GLP-1. |
| High | Distinguish gross revenue, value-added capture, and operating-profit proxy in separate views. | Avoid mixing economic concepts in one ranking. |
| High | Add a company archetype tracker for Physical Intelligence. | Keep it categorical unless company evidence is audited. |
| Medium | Add OECD TiVA and UN Comtrade enrichment scripts. | Useful for batteries, semiconductors, solar, and manufacturing-heavy platforms. |
| Medium | Add patent-assignee enrichment. | Useful for IP-owner and licensing roles. |
| Medium | Add Monte Carlo uncertainty simulation. | Convert low/base/high ranges into scenario distributions. |
| Low | Add a network graph of paper to institution to platform to country to market. | Useful for storytelling after assumptions mature. |

## Changelog

| Date | Change | Author | Reason | Files affected |
|---|---|---|---|---|
| 2026-06-04 | Reframed the dashboard around the Physical Intelligence thesis, added thesis-link CSVs, and kept country value capture as a stress-test layer. | Codex | User requested a thesis-driven presentation about the next AI wave for science. | Notebook, HTML, CSV outputs, Markdown guide |
