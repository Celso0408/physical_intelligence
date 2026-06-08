# Billionaire Papers and Physical Intelligence

**Billionaire Papers and Physical Intelligence** is a standalone interactive dashboard that explores how breakthrough scientific and technical papers can become platform technologies, how those platforms connect to Physical Intelligence / Physical AI, and how economic value capture can differ from research origin.

The core thesis is deliberately framed as a hypothesis to be supported and stress-tested:

> Physical Intelligence may become a major next wave for AI and science because earlier platform breakthroughs already created the technical base for AI systems that perceive, simulate, plan, manipulate, manufacture, synthesize, test, measure, and learn from the physical world.

This project is not investment advice, policy advice, or a definitive economic audit. Revenue, funding, country-benefit, and value-capture estimates are model-based and should be treated as directional until independently verified.

All Rights Reserved.

## Live Dashboard

The GitHub Pages entry point is:

```text
index.html
```

If this repository is published with GitHub Pages, the dashboard will load directly from the repository Pages URL.

## What The Dashboard Shows

The presentation is organized around a paper-to-power story:

```text
Paper -> Platform -> Machine -> Lab/Factory -> Market -> Country
```

Key views include:

- A thesis-driven hero section for first-time viewers.
- A six-act narrative explaining the transition from breakthrough papers to Physical Intelligence.
- Platform, capability, and domain charts for Physical Intelligence.
- Active Physical AI company landscape by country, sub-field, funding, and strategic region.
- Research-origin versus beneficiary/value-capture views for the US, EU, and China.
- A dataset explorer for both papers and companies.
- Downloadable CSVs, methodology notes, and a reproducible Colab notebook.

## Main Files

| File | Purpose |
|---|---|
| `index.html` | Self-contained interactive dashboard for GitHub Pages. |
| `billionaire_papers_dashboard.ipynb` | Reproducible Google Colab notebook. |
| `DASHBOARD_INSTRUCTIONS.md` | Living methodology, data model, design system, and update guide. |
| `requirements.txt` | Python dependencies used by the notebook/build workflow. |
| `build_billionaire_papers_dashboard.py` | Dashboard generation script. |
| `.nojekyll` | Ensures GitHub Pages serves static files directly. |

## Core Data Files

| File | Purpose |
|---|---|
| `billionaire_papers_1976_2026_china_benefit_updated.csv` | Preferred source paper table with China-benefit fields. |
| `billionaire_papers_1976_2026.csv` | Original/fallback source paper table. |
| `physical_ai_companies_active_updated_investments.csv` | Active Physical AI company source data with investment estimates. |
| `physical_ai_companies_active_clean.csv` | Cleaned active company table used in the dashboard. |
| `physical_intelligence_thesis_links.csv` | Paper-to-platform-to-capability thesis mapping. |
| `physical_intelligence_domain_summary.csv` | Physical Intelligence domain summary. |

## Derived Output Tables

| File | Purpose |
|---|---|
| `paper_benefit_assumptions_template.csv` | Editable assumptions template for country-level value capture. |
| `paper_country_benefit_estimates.csv` | Role-level low/base/high value-capture estimates. |
| `paper_country_benefit_long.csv` | Long-form country benefit table. |
| `paper_country_benefit_china_update_long.csv` | China-specific benefit layer. |
| `country_summary.csv` | Aggregated beneficiary-country summary. |
| `china_value_capture_summary.csv` | China capture-share summary. |
| `origin_country_summary.csv` | Research-origin country summary. |
| `origin_to_beneficiary_flow.csv` | Origin-to-platform-to-beneficiary flow table. |
| `field_country_summary.csv` | Field and country summary. |
| `public_private_spillover_summary.csv` | Public/private/mixed research-origin summary. |
| `physical_ai_company_country_summary.csv` | Active Physical AI country exposure summary. |
| `physical_ai_company_subfield_summary.csv` | Active Physical AI company and funding by sub-field. |
| `physical_ai_company_region_summary.csv` | Strategic-region comparison. |
| `quality_check_report.csv` | Data-quality and model-readiness checks. |

## Publish On GitHub Pages

1. Create a GitHub repository.
2. Upload the contents of this folder to the repository root.
3. In GitHub, open **Settings -> Pages**.
4. Set the source to the default branch and root folder.
5. Save, then wait for GitHub Pages to publish the site.

The repository root should contain `index.html`. If `index.html` is inside a subfolder, GitHub Pages will not load the dashboard as the home page unless Pages is configured to serve from that subfolder.

## Reproducibility

The dashboard is designed to be reproducible from the notebook and source data:

1. Open `billionaire_papers_dashboard.ipynb` in Google Colab.
2. Upload or mount the CSV files listed above.
3. Run the notebook cells in order.
4. Export the generated standalone HTML.
5. Replace `index.html` with the newly exported dashboard when publishing updates.

For implementation details, assumptions, and chart requirements, see:

```text
DASHBOARD_INSTRUCTIONS.md
```

## Methodology Notes

- A "billionaire paper" is defined as a scientific or technical publication that plausibly enabled more than USD 1B in cumulative commercial revenue or economic value after publication.
- Research origin is not the same as value capture.
- Country benefit estimates use assumptions about commercialization, manufacturing, IP, cloud/data, adoption, and supply-chain roles.
- Physical Intelligence classifications are rule-based and auditable, not definitive.
- Funding estimates for Physical AI companies may mix total funding, latest rounds, IPO proceeds, acquisition values, and reported ranges.
- All economic estimates should be audited before being used for academic claims, policy claims, or investment decisions.

## License And Rights

Copyright PhD. Celso Ricardo Caldeira Rego.

All Rights Reserved.

