#!/usr/bin/env python3
"""Build the billionaire papers dashboard and supporting CSV artifacts."""

from __future__ import annotations

import html
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

import nbformat as nbf
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio


INPUT_CSV = "billionaire_papers_1976_2026.csv"
CHINA_UPDATED_INPUT_CSV = "billionaire_papers_1976_2026_china_benefit_updated.csv"
CHINA_BENEFIT_LONG_CSV = "paper_country_benefit_china_update_long.csv"
OUTPUT_HTML = "billionaire_papers_dashboard.html"
OUTPUT_NOTEBOOK = "billionaire_papers_dashboard.ipynb"
INSTRUCTIONS_MD = "DASHBOARD_INSTRUCTIONS.md"
ASSUMPTIONS_CSV = "paper_benefit_assumptions_template.csv"
BENEFIT_ESTIMATES_CSV = "paper_country_benefit_estimates.csv"
BENEFIT_LONG_CSV = "paper_country_benefit_long.csv"
COUNTRY_SUMMARY_CSV = "country_summary.csv"
CHINA_SUMMARY_CSV = "china_value_capture_summary.csv"
ORIGIN_COUNTRY_SUMMARY_CSV = "origin_country_summary.csv"
ORIGIN_TO_BENEFICIARY_FLOW_CSV = "origin_to_beneficiary_flow.csv"
FIELD_COUNTRY_SUMMARY_CSV = "field_country_summary.csv"
PUBLIC_PRIVATE_SPILLOVER_SUMMARY_CSV = "public_private_spillover_summary.csv"
QUALITY_CHECK_REPORT_CSV = "quality_check_report.csv"
PHYSICAL_INTELLIGENCE_LINKS_CSV = "physical_intelligence_thesis_links.csv"
PHYSICAL_INTELLIGENCE_DOMAIN_SUMMARY_CSV = "physical_intelligence_domain_summary.csv"
PHYSICAL_AI_COMPANIES_CSV = "physical_ai_companies_active_updated_investments.csv"
PHYSICAL_AI_COMPANIES_CLEAN_CSV = "physical_ai_companies_active_clean.csv"
PHYSICAL_AI_COUNTRY_SUMMARY_CSV = "physical_ai_company_country_summary.csv"
PHYSICAL_AI_SUBFIELD_SUMMARY_CSV = "physical_ai_company_subfield_summary.csv"
PHYSICAL_AI_REGION_SUMMARY_CSV = "physical_ai_company_region_summary.csv"
REQUIREMENTS_TXT = "requirements.txt"

REQUIRED_COLUMNS = [
    "ID",
    "Confidence_tier",
    "Broad_area",
    "Field_or_platform",
    "Paper_or_discovery",
    "Country_or_countries",
    "Institution_at_publication",
    "Authors",
    "Year",
    "DOI_or_link",
    "Public_or_private",
    "Organization_type",
    "Billionaire_rationale",
    "Notes",
]

ASSUMPTION_COLUMNS = [
    "paper_id",
    "paper_or_discovery",
    "field_or_platform",
    "beneficiary_country",
    "beneficiary_country_iso3",
    "beneficiary_role",
    "enabled_revenue_low_usd",
    "enabled_revenue_base_usd",
    "enabled_revenue_high_usd",
    "paper_attribution_low",
    "paper_attribution_base",
    "paper_attribution_high",
    "country_capture_share_low",
    "country_capture_share_base",
    "country_capture_share_high",
    "role_margin_low",
    "role_margin_base",
    "role_margin_high",
    "benefit_type",
    "confidence_level",
    "evidence_summary",
    "source_1",
    "source_2",
    "source_3",
    "analyst_notes",
    "last_updated",
]

ALLOWED_ROLES = [
    "research_origin",
    "ip_owner",
    "patent_assignee",
    "licensing",
    "commercialization",
    "company_headquarters",
    "manufacturing",
    "supply_chain",
    "equipment_supplier",
    "manufacturing_equipment",
    "cloud_compute",
    "platform_operator",
    "standards_ecosystem",
    "adoption_market",
    "deployment_base",
    "health_system_savings",
    "agricultural_yield_gain",
    "consumer_surplus",
    "data_generation",
    "talent_pipeline",
    "strategic_capability",
    "software_ecosystem",
    "other",
]

EU_MEMBER_ISO3 = {
    "AUT",
    "BEL",
    "BGR",
    "HRV",
    "CYP",
    "CZE",
    "DNK",
    "EST",
    "FIN",
    "FRA",
    "DEU",
    "GRC",
    "HUN",
    "IRL",
    "ITA",
    "LVA",
    "LTU",
    "LUX",
    "MLT",
    "NLD",
    "POL",
    "PRT",
    "ROU",
    "SVK",
    "SVN",
    "ESP",
    "SWE",
}

ALLOWED_BENEFIT_TYPES = [
    "gross_revenue_capture",
    "value_added_capture",
    "operating_profit_proxy",
    "cost_savings",
    "consumer_surplus_proxy",
    "public_health_value",
    "strategic_capability",
]

ROLE_WEIGHT_TEMPLATES = {
    "pharma_biotech_vaccines": {
        "company_headquarters": 0.30,
        "ip_owner": 0.20,
        "manufacturing": 0.10,
        "adoption_market": 0.25,
        "health_system_savings": 0.05,
        "research_origin": 0.10,
    },
    "batteries_materials_semiconductors_hardware": {
        "manufacturing": 0.30,
        "company_headquarters": 0.20,
        "supply_chain": 0.15,
        "equipment_supplier": 0.10,
        "adoption_market": 0.15,
        "research_origin": 0.10,
    },
    "software_ai_cloud_internet_platforms": {
        "platform_operator": 0.30,
        "company_headquarters": 0.25,
        "cloud_compute": 0.15,
        "adoption_market": 0.15,
        "data_generation": 0.05,
        "research_origin": 0.10,
    },
    "communications_standards_cryptography_protocols": {
        "standards_ecosystem": 0.25,
        "company_headquarters": 0.20,
        "adoption_market": 0.20,
        "equipment_supplier": 0.15,
        "ip_owner": 0.10,
        "research_origin": 0.10,
    },
    "agriculture_crop_biotechnology": {
        "company_headquarters": 0.25,
        "commercialization": 0.15,
        "adoption_market": 0.25,
        "agricultural_yield_gain": 0.20,
        "research_origin": 0.10,
        "supply_chain": 0.05,
    },
    "robotics_industrial_automation": {
        "manufacturing": 0.25,
        "company_headquarters": 0.20,
        "deployment_base": 0.25,
        "equipment_supplier": 0.10,
        "software_ecosystem": 0.10,
        "research_origin": 0.10,
    },
}

COUNTRY_ALIASES = {
    "usa": ("United States", "USA"),
    "u.s.": ("United States", "USA"),
    "u.s.a.": ("United States", "USA"),
    "united states": ("United States", "USA"),
    "uk": ("United Kingdom", "GBR"),
    "u.k.": ("United Kingdom", "GBR"),
    "united kingdom": ("United Kingdom", "GBR"),
    "england": ("United Kingdom", "GBR"),
    "japan": ("Japan", "JPN"),
    "france": ("France", "FRA"),
    "belgium": ("Belgium", "BEL"),
    "australia": ("Australia", "AUS"),
    "switzerland": ("Switzerland", "CHE"),
    "germany": ("Germany", "DEU"),
    "canada": ("Canada", "CAN"),
    "lebanon": ("Lebanon", "LBN"),
    "sweden": ("Sweden", "SWE"),
    "austria": ("Austria", "AUT"),
    "china": ("China", "CHN"),
    "taiwan": ("Taiwan", "TWN"),
    "netherlands": ("Netherlands", "NLD"),
    "south korea": ("South Korea", "KOR"),
    "korea": ("South Korea", "KOR"),
    "republic of korea": ("South Korea", "KOR"),
    "ireland": ("Ireland", "IRL"),
    "singapore": ("Singapore", "SGP"),
    "israel": ("Israel", "ISR"),
    "denmark": ("Denmark", "DNK"),
    "norway": ("Norway", "NOR"),
    "india": ("India", "IND"),
    "chile": ("Chile", "CHL"),
    "argentina": ("Argentina", "ARG"),
    "brazil": ("Brazil", "BRA"),
    "unknown": ("Unknown / online", ""),
    "unknown / online": ("Unknown / online", ""),
    "online": ("Unknown / online", ""),
}

CASE_STUDY_KEYWORDS = [
    ("Lithium-ion battery cathode / LiCoO2", ["LiCoO2", "layered oxide"]),
    ("LiFePO4 battery cathode", ["Phospho-olivines", "LFP cathode"]),
    ("Transformer architecture", ["Attention Is All You Need", "Transformers"]),
    ("mRNA nucleoside modification", ["Nucleoside-modified mRNA", "nucleoside modification"]),
    ("PCR", ["PCR molecular", "beta-globin"]),
    ("CRISPR-Cas9", ["CRISPR-Cas9", "dual-RNA-guided"]),
    ("OLED", ["OLED", "Organic electroluminescent"]),
    ("Blue LED", ["blue-light-emitting", "GaN LED"]),
    ("PageRank", ["PageRank"]),
    ("Ethernet", ["Ethernet"]),
    ("Checkpoint immunotherapy", ["CTLA-4", "PD-L1", "checkpoint"]),
    ("Sofosbuvir", ["Sofosbuvir"]),
    ("GLP-1 biology", ["GLP-1"]),
]

EXPECTED_CHINA_BENEFICIARY_IDS = {
    5,
    7,
    19,
    22,
    24,
    25,
    26,
    28,
    31,
    38,
    39,
    41,
    47,
    48,
    49,
    50,
    51,
    53,
    54,
    55,
    57,
    59,
}

DESIGN_COLORS = {
    "origin": "#2563eb",
    "value_capture": "#d97706",
    "china": "#dc2626",
    "public_origin": "#2563eb",
    "private_origin": "#7c3aed",
    "mixed_origin": "#0f766e",
    "warning": "#b45309",
    "success": "#15803d",
    "uncertain": "rgba(180, 83, 9, 0.24)",
    "ink": "#111827",
    "muted": "#4b5563",
}

MODEBAR_CONFIG = {"displaylogo": False, "responsive": True}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def select_input_csv() -> str:
    """Prefer the China-updated main CSV when it is present."""
    if Path(CHINA_UPDATED_INPUT_CSV).exists():
        return CHINA_UPDATED_INPUT_CSV
    return INPUT_CSV


def split_urls(value: object) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*;\s*", text) if part.strip()]


def pct_to_fraction(value: object) -> float:
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return np.nan
    return float(number) / 100.0


def normalize_country_name(country_text: object) -> tuple[str, str]:
    """Return standardized country name and ISO-3 code."""
    text = clean_text(country_text)
    if not text:
        return "", ""
    key = text.lower().strip()
    key = re.sub(r"\s+", " ", key)
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    try:
        import pycountry

        country = pycountry.countries.lookup(text)
        return country.name, country.alpha_3
    except Exception:
        return text, ""


def split_origin_countries(country_or_countries: object) -> list[dict[str, str]]:
    """Split multi-country strings into standardized country records."""
    text = clean_text(country_or_countries)
    if not text:
        return [{"country": "", "iso3": "", "raw": ""}]
    parts = [p.strip() for p in re.split(r"\s*;\s*|\s+\+\s+", text) if p.strip()]
    records = []
    for part in parts:
        country, iso3 = normalize_country_name(part)
        records.append({"country": country, "iso3": iso3, "raw": part})
    return records or [{"country": "", "iso3": "", "raw": text}]


def parse_year(value: object) -> float:
    text = clean_text(value)
    matches = re.findall(r"(?:19|20)\d{2}", text)
    if matches:
        return float(matches[0])
    return np.nan


def format_usd(value: object) -> str:
    if pd.isna(value):
        return "Not estimated"
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000_000:
        return f"{sign}${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:,.0f}"


def format_number(value: object) -> str:
    if pd.isna(value):
        return "n/a"
    value = float(value)
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def short_label(value: object, length: int = 48) -> str:
    text = clean_text(value)
    if len(text) <= length:
        return text
    return text[: max(0, length - 1)].rstrip() + "..."


def format_role_label(value: object) -> str:
    text = clean_text(value).replace("_", " ")
    if not text:
        return "unspecified role"
    replacements = {
        "ip": "IP",
        "ai": "AI",
    }
    return " ".join(replacements.get(part.lower(), part.lower()) for part in text.split())


def validate_schema(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def load_source_csv(path: str | Path = INPUT_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    validate_schema(df)
    return df


def ensure_china_source_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    alias_map = {
        "China_beneficiary_roles": "China_beneficiary_role",
        "China_value_capture_rationale": "China_estimate_basis",
        "China_evidence_sources": "China_evidence_urls",
        "China_evidence_confidence": "China_benefit_confidence",
        "China_benefit_status": "China_assumption_status",
    }
    for old, new in alias_map.items():
        if new not in df.columns and old in df.columns:
            df[new] = df[old]
    required_china_cols = [
        "China_beneficiary_flag",
        "China_beneficiary_role",
        "China_value_capture_channels",
        "China_benefit_strength",
        "China_benefit_confidence",
        "China_revenue_capture_share_low_pct",
        "China_revenue_capture_share_base_pct",
        "China_revenue_capture_share_high_pct",
        "China_estimate_basis",
        "China_evidence_urls",
        "China_value_capture_notes",
        "China_assumption_status",
    ]
    for col in required_china_cols:
        if col not in df.columns:
            df[col] = ""
    if "Origin_country_or_countries" not in df.columns:
        df["Origin_country_or_countries"] = df["Country_or_countries"]
    return df


def clean_papers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = ensure_china_source_columns(df)
    cleaned["paper_id"] = pd.to_numeric(cleaned["ID"], errors="coerce").astype("Int64")
    cleaned["confidence_tier_clean"] = cleaned["Confidence_tier"].map(clean_text)
    cleaned["broad_area_clean"] = cleaned["Broad_area"].map(clean_text)
    cleaned["field_clean"] = cleaned["Field_or_platform"].map(clean_text)
    cleaned["year_int"] = cleaned["Year"].map(parse_year).astype("Int64")
    cleaned["decade"] = cleaned["year_int"].map(lambda y: f"{int(y // 10 * 10)}s" if pd.notna(y) else "")
    cleaned["origin_country_raw"] = cleaned["Origin_country_or_countries"].map(clean_text)
    origin_records = cleaned["Origin_country_or_countries"].map(split_origin_countries)
    cleaned["origin_country_list"] = origin_records.map(lambda rs: "; ".join(r["country"] for r in rs if r["country"]))
    cleaned["origin_country_iso3_list"] = origin_records.map(lambda rs: "; ".join(r["iso3"] for r in rs if r["iso3"]))
    cleaned["origin_country_primary"] = origin_records.map(lambda rs: rs[0]["country"] if rs else "")
    cleaned["origin_country_primary_iso3"] = origin_records.map(lambda rs: rs[0]["iso3"] if rs else "")
    cleaned["institution_clean"] = cleaned["Institution_at_publication"].map(clean_text)
    cleaned["org_type_clean"] = cleaned["Organization_type"].map(clean_text)
    cleaned["public_private_clean"] = cleaned["Public_or_private"].map(clean_text)
    cleaned["doi_or_link_clean"] = cleaned["DOI_or_link"].map(clean_text)
    cleaned["has_china_origin"] = cleaned["origin_country_list"].str.contains(r"\bChina\b", case=False, na=False)
    china_flag_text = cleaned["China_beneficiary_flag"].map(clean_text).str.lower()
    cleaned["has_china_beneficiary"] = china_flag_text.isin(["yes", "true", "1"]) | cleaned[
        "China_revenue_capture_share_base_pct"
    ].map(lambda value: pd.notna(pd.to_numeric(value, errors="coerce")))

    long_rows = []
    for _, row in cleaned.iterrows():
        for rec in split_origin_countries(row["Origin_country_or_countries"]):
            long_rows.append(
                {
                    "paper_id": row["paper_id"],
                    "paper_or_discovery": row["Paper_or_discovery"],
                    "broad_area_clean": row["broad_area_clean"],
                    "field_clean": row["field_clean"],
                    "year_int": row["year_int"],
                    "decade": row["decade"],
                    "origin_country_raw": row["origin_country_raw"],
                    "origin_country": rec["country"],
                    "origin_country_iso3": rec["iso3"],
                    "origin_country_normalization_failed": bool(rec["country"] and not rec["iso3"]),
                }
            )
    origin_long = pd.DataFrame(long_rows)
    return cleaned, origin_long


def canonical_china_role(role_text: object, channel_text: object = "") -> str:
    text = f"{clean_text(role_text)} {clean_text(channel_text)}".lower()
    if any(word in text for word in ["battery", "magnet", "refining", "manufacturing", "panel", "module", "cell", "camera", "electronics"]):
        return "manufacturing"
    if any(word in text for word in ["telecom", "standards", "mobile-network", "5g", "4g"]):
        return "standards_ecosystem"
    if any(word in text for word in ["supply", "materials", "cathode", "anode", "rare-earth", "active materials"]):
        return "supply_chain"
    if any(word in text for word in ["cloud", "data center", "internet services", "platform"]):
        return "cloud_compute"
    if any(word in text for word in ["deployment", "services", "applications", "adoption", "domestic", "use cases", "automation", "optimization"]):
        return "adoption_market"
    return "other"


def load_china_benefit_update(path: str | Path = CHINA_BENEFIT_LONG_CSV) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8-sig")
    required = [
        "Paper_ID",
        "Paper_or_discovery",
        "Field_or_platform",
        "Origin_country_or_countries",
        "Beneficiary_country",
        "Beneficiary_country_iso3",
        "Beneficiary_role",
        "Value_capture_channels",
        "Benefit_strength",
        "Benefit_confidence",
        "Revenue_capture_share_low_pct",
        "Revenue_capture_share_base_pct",
        "Revenue_capture_share_high_pct",
        "Estimate_basis",
        "Evidence_urls",
        "Value_capture_notes",
        "Assumption_status",
        "Update_date",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"China benefit update is missing columns: {', '.join(missing)}")
    out = df.copy()
    out["paper_id"] = pd.to_numeric(out["Paper_ID"], errors="coerce").astype("Int64")
    out["beneficiary_country"] = out["Beneficiary_country"].map(clean_text)
    out["beneficiary_country_iso3"] = out["Beneficiary_country_iso3"].map(clean_text)
    out["beneficiary_role_canonical"] = out.apply(
        lambda row: canonical_china_role(row["Beneficiary_role"], row["Value_capture_channels"]), axis=1
    )
    for scenario in ["low", "base", "high"]:
        source_col = f"Revenue_capture_share_{scenario}_pct"
        out[f"china_capture_share_{scenario}"] = out[source_col].map(pct_to_fraction)
    out["share_band_label"] = out.apply(
        lambda row: (
            f"{row['Revenue_capture_share_low_pct']:.0f}-{row['Revenue_capture_share_high_pct']:.0f}%"
            if pd.notna(row["Revenue_capture_share_low_pct"]) and pd.notna(row["Revenue_capture_share_high_pct"])
            else ""
        ),
        axis=1,
    )
    return out


def add_china_update_to_assumptions(assumptions: pd.DataFrame, china_update: pd.DataFrame) -> pd.DataFrame:
    if china_update.empty:
        return assumptions
    assumptions = assumptions.copy()
    existing_china = assumptions["beneficiary_country_iso3"].map(clean_text).eq("CHN")
    assumptions = assumptions[~existing_china].copy()

    rows = []
    for _, row in china_update.iterrows():
        urls = split_urls(row["Evidence_urls"])
        rows.append(
            {
                "paper_id": int(row["paper_id"]),
                "paper_or_discovery": row["Paper_or_discovery"],
                "field_or_platform": row["Field_or_platform"],
                "beneficiary_country": "China",
                "beneficiary_country_iso3": "CHN",
                "beneficiary_role": row["beneficiary_role_canonical"],
                "enabled_revenue_low_usd": np.nan,
                "enabled_revenue_base_usd": np.nan,
                "enabled_revenue_high_usd": np.nan,
                "paper_attribution_low": np.nan,
                "paper_attribution_base": np.nan,
                "paper_attribution_high": np.nan,
                "country_capture_share_low": row["china_capture_share_low"],
                "country_capture_share_base": row["china_capture_share_base"],
                "country_capture_share_high": row["china_capture_share_high"],
                "role_margin_low": np.nan,
                "role_margin_base": np.nan,
                "role_margin_high": np.nan,
                "benefit_type": "value_added_capture",
                "confidence_level": f"china_{clean_text(row['Benefit_confidence']).lower().replace(' ', '_')}",
                "evidence_summary": clean_text(row["Estimate_basis"]),
                "source_1": urls[0] if len(urls) > 0 else "",
                "source_2": urls[1] if len(urls) > 1 else "",
                "source_3": urls[2] if len(urls) > 2 else "",
                "analyst_notes": (
                    f"China update: strength={clean_text(row['Benefit_strength'])}; "
                    f"raw role={clean_text(row['Beneficiary_role'])}; "
                    f"channels={clean_text(row['Value_capture_channels'])}; "
                    f"notes={clean_text(row['Value_capture_notes'])}; "
                    f"status={clean_text(row['Assumption_status'])}"
                ),
                "last_updated": clean_text(row["Update_date"]) or date.today().isoformat(),
            }
        )
    china_rows = pd.DataFrame(rows, columns=ASSUMPTION_COLUMNS)
    return pd.concat([assumptions, china_rows], ignore_index=True)


def build_china_summary(china_update: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "metric",
        "value",
    ]
    if china_update.empty:
        return pd.DataFrame(columns=cols)
    high_or_better = china_update["Benefit_confidence"].map(clean_text).isin(["High", "Medium-high"])
    very_high_strength = china_update["Benefit_strength"].map(clean_text).eq("Very high")
    base_share = pd.to_numeric(china_update["Revenue_capture_share_base_pct"], errors="coerce")
    top_row = china_update.loc[base_share.idxmax()] if base_share.notna().any() else None
    rows = [
        {"metric": "China beneficiary papers", "value": f"{china_update['paper_id'].nunique():,}"},
        {"metric": "High or medium-high confidence rows", "value": f"{int(high_or_better.sum()):,}"},
        {"metric": "Very high strength rows", "value": f"{int(very_high_strength.sum()):,}"},
        {"metric": "Average base capture share", "value": f"{base_share.mean():.1f}%"},
        {"metric": "Median base capture share", "value": f"{base_share.median():.1f}%"},
    ]
    if top_row is not None:
        rows.append(
            {
                "metric": "Highest base capture share",
                "value": f"{clean_text(top_row['Field_or_platform'])}: {float(top_row['Revenue_capture_share_base_pct']):.0f}%",
            }
        )
    return pd.DataFrame(rows, columns=cols)


CORE_PLATFORM_KEYWORDS = [
    ("Batteries", ["battery", "lithium", "cathode", "lico", "lifepo", "lfp"]),
    ("Semiconductors", ["semiconductor", "finfet", "photoresist", "lithography", "risc"]),
    ("Solar", ["solar", "photovoltaic", "perc"]),
    ("Robotics", ["robot", "slam", "autonomous robotics", "ros"]),
    ("Computer vision", ["computer vision", "object detection", "imagenet", "alexnet", "resnet", "yolo", "image sensor"]),
    ("Transformers and deep learning", ["transformer", "bert", "lstm", "deep learning", "diffusion", "reinforcement"]),
    ("AI for biology", ["alphafold", "protein structure", "ai for biology"]),
    ("Cloud infrastructure", ["cloud", "file system", "mapreduce", "bigtable", "data infrastructure"]),
    ("Molecular biology", ["pcr", "sequencing", "crispr", "mrna", "rna", "genomics", "antibody", "phage"]),
    ("Automation", ["robot", "automation", "autonomous", "reinforcement", "slam"]),
    ("Materials science", ["materials", "magnet", "oled", "quantum dot", "led", "cathode", "photoresist"]),
]


def _row_text(row: pd.Series) -> str:
    return " ".join(
        [
            clean_text(row.get("Broad_area", "")),
            clean_text(row.get("Field_or_platform", "")),
            clean_text(row.get("Paper_or_discovery", "")),
            clean_text(row.get("Billionaire_rationale", "")),
        ]
    ).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def core_platform_presence(cleaned: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for platform, keywords in CORE_PLATFORM_KEYWORDS:
        mask = cleaned.apply(lambda row: _has_any(_row_text(row), keywords), axis=1)
        rows.append(
            {
                "platform": platform,
                "matched_papers": int(mask.sum()),
                "status": "present" if mask.any() else "gap",
            }
        )
    return pd.DataFrame(rows)


def classify_pi_platform_family(text: str) -> str:
    if _has_any(text, ["battery", "lithium", "cathode", "energy materials"]):
        return "Batteries and energy storage"
    if _has_any(text, ["solar", "photovoltaic", "perc"]):
        return "Solar and energy systems"
    if _has_any(text, ["semiconductor", "finfet", "photoresist", "lithography", "cmos", "oled", "display", "led", "quantum dot", "spintronics", "magnet"]):
        return "Semiconductors, sensors and displays"
    if _has_any(text, ["robot", "slam", "ros", "object detection", "computer vision", "yolo", "autonomous"]):
        return "Robotics, autonomy and perception"
    if _has_any(text, ["transformer", "bert", "lstm", "diffusion", "deep learning", "reinforcement learning", "alphafold", "foundation model"]):
        return "AI models and prediction"
    if _has_any(text, ["cloud", "file system", "mapreduce", "bigtable", "ethernet", "wireless", "mimo", "turbo codes", "web", "pagerank", "risc"]):
        return "Compute, data and network infrastructure"
    if _has_any(text, ["pcr", "sequencing", "genomics", "crispr", "mrna", "rna", "protein", "antibody", "phage", "biomarker", "car-t", "vaccine", "drug", "pharma", "biopharma", "therapy", "glp-1", "sofosbuvir"]):
        return "Molecular biology and bioengineering"
    if _has_any(text, ["crop", "plant", "agricultur", "glyphosate", "bt insect"]):
        return "Agricultural biotechnology"
    if _has_any(text, ["cryptography", "rsa", "diffie", "bitcoin", "blockchain"]):
        return "Digital trust and market infrastructure"
    return "Other enabling platform"


def classify_pi_capabilities(text: str) -> list[str]:
    capabilities: list[str] = []
    if _has_any(text, ["cmos", "image sensor", "computer vision", "object detection", "imagenet", "alexnet", "resnet", "yolo", "slam", "sequencing", "pcr", "diagnostic", "genomics"]):
        capabilities.append("Perceive and measure")
    if _has_any(text, ["transformer", "bert", "lstm", "diffusion", "deep learning", "alphafold", "protein structure", "reinforcement learning", "pagerank", "search"]):
        capabilities.append("Predict, model and generate")
    if _has_any(text, ["robot", "slam", "ros", "autonomous", "reinforcement learning", "game ai", "control"]):
        capabilities.append("Plan and control")
    if _has_any(text, ["robot", "manufacturing", "semiconductor", "photoresist", "lithography", "battery", "cathode", "solar", "led", "oled", "display", "magnet", "materials", "crop", "plant"]):
        capabilities.append("Manipulate and manufacture")
    if _has_any(text, ["pcr", "sequencing", "crispr", "mrna", "rna", "protein", "antibody", "phage", "drug", "vaccine", "chemistry", "materials", "quantum dot", "cathode"]):
        capabilities.append("Synthesize and test")
    if _has_any(text, ["cloud", "file system", "mapreduce", "bigtable", "data", "computer vision", "genomics", "sequencing", "sensor", "internet", "web"]):
        capabilities.append("Learn from physical-world data")
    if _has_any(text, ["cryptography", "rsa", "diffie", "bitcoin", "blockchain", "network security"]):
        capabilities.append("Secure and coordinate infrastructure")
    return capabilities or ["Indirect enabling context"]


def classify_science_domains(text: str) -> list[str]:
    domains: list[str] = []
    if _has_any(text, ["biology", "genomic", "pcr", "mrna", "rna", "antibody", "protein", "crispr", "vaccine", "pharma", "therapy", "cancer", "glp-1", "alphafold", "cell therapy", "diagnostic"]):
        domains.append("Biology and health")
    if _has_any(text, ["chemistry", "materials", "battery", "cathode", "quantum dot", "magnet", "oled", "photoresist", "semiconductor", "led"]):
        domains.append("Chemistry and materials")
    if _has_any(text, ["robot", "slam", "ros", "automation", "autonomous", "object detection", "computer vision", "reinforcement"]):
        domains.append("Robotics and automation")
    if _has_any(text, ["robot", "slam", "autonomous", "wireless", "mimo", "sensor", "battery", "reinforcement", "computer vision"]):
        domains.append("Aerospace and mobility")
    if _has_any(text, ["energy", "battery", "solar", "led", "lithium", "perc"]):
        domains.append("Energy and climate")
    if _has_any(text, ["crop", "plant", "agricultur", "glyphosate", "bt insect"]):
        domains.append("Agriculture")
    if _has_any(text, ["manufacturing", "semiconductor", "photoresist", "lithography", "finfet", "display", "oled", "led", "robot", "materials"]):
        domains.append("Manufacturing")
    if _has_any(text, ["cloud", "file system", "mapreduce", "bigtable", "ethernet", "web", "cryptography", "wireless", "mimo", "turbo", "bitcoin", "blockchain"]):
        domains.append("Digital infrastructure")
    return domains or ["Cross-domain science infrastructure"]


def classify_pi_relevance(platform_family: str, capabilities: list[str]) -> str:
    if platform_family in {"Digital trust and market infrastructure", "Other enabling platform"}:
        return "Adjacent economic platform"
    if "Secure and coordinate infrastructure" in capabilities:
        return "Enabling digital infrastructure"
    if platform_family in {"Compute, data and network infrastructure"}:
        return "Enabling digital infrastructure"
    return "Direct physical-intelligence substrate"


def build_physical_intelligence_links(cleaned: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in cleaned.iterrows():
        text = _row_text(row)
        platform_family = classify_pi_platform_family(text)
        capabilities = classify_pi_capabilities(text)
        domains = classify_science_domains(text)
        relevance = classify_pi_relevance(platform_family, capabilities)
        for capability in capabilities:
            for domain in domains:
                rows.append(
                    {
                        "paper_id": int(row["paper_id"]),
                        "year": row["year_int"],
                        "paper_or_discovery": row["Paper_or_discovery"],
                        "field_or_platform": row["Field_or_platform"],
                        "broad_area": row["broad_area_clean"],
                        "origin_country_list": row["origin_country_list"],
                        "public_private_origin": row["public_private_clean"],
                        "pi_platform_family": platform_family,
                        "pi_capability": capability,
                        "science_acceleration_domain": domain,
                        "pi_relevance": relevance,
                        "classification_basis": "Rule-based keyword mapping for the Physical Intelligence thesis layer; audit before using as a formal taxonomy.",
                    }
                )
    columns = [
        "paper_id",
        "year",
        "paper_or_discovery",
        "field_or_platform",
        "broad_area",
        "origin_country_list",
        "public_private_origin",
        "pi_platform_family",
        "pi_capability",
        "science_acceleration_domain",
        "pi_relevance",
        "classification_basis",
    ]
    return pd.DataFrame(rows, columns=columns)


def build_physical_intelligence_domain_summary(pi_links: pd.DataFrame) -> pd.DataFrame:
    columns = ["science_acceleration_domain", "papers", "platform_families", "capabilities", "direct_papers"]
    if pi_links.empty:
        return pd.DataFrame(columns=columns)
    grouped = pi_links.groupby("science_acceleration_domain", dropna=False)
    summary = grouped.agg(
        papers=("paper_id", "nunique"),
        platform_families=("pi_platform_family", lambda s: "; ".join(sorted({clean_text(v) for v in s if clean_text(v)})[:5])),
        capabilities=("pi_capability", lambda s: "; ".join(sorted({clean_text(v) for v in s if clean_text(v)})[:5])),
    ).reset_index()
    direct = (
        pi_links[pi_links["pi_relevance"].eq("Direct physical-intelligence substrate")]
        .groupby("science_acceleration_domain")["paper_id"]
        .nunique()
    )
    summary["direct_papers"] = summary["science_acceleration_domain"].map(direct).fillna(0).astype(int)
    return summary[columns].sort_values(["direct_papers", "papers"], ascending=False)


def split_company_countries(value: object) -> list[tuple[str, str]]:
    text = clean_text(value)
    if not text:
        return [("Unknown / mixed", "")]
    parts = [part.strip() for part in re.split(r"\s*(?:/|;|,|\+|&)\s*", text) if part.strip()]
    normalized = []
    for part in parts or [text]:
        country, iso3 = normalize_country_name(part)
        normalized.append((country or part, iso3))
    deduped = list(dict.fromkeys(normalized))
    return deduped or [("Unknown / mixed", "")]


def classify_company_subfield(row: pd.Series) -> str:
    text = " ".join(
        [
            clean_text(row.get("Startup Name", "")),
            clean_text(row.get("Core Scientific Field", "")),
            clean_text(row.get("How Physical Intelligence is Used", "")),
            clean_text(row.get("Physical_AI_Fit", "")),
        ]
    ).lower()
    if any(k in text for k in ["humanoid", "embodied", "bipedal", "foundation model", "robot foundation"]):
        return "Humanoids & robot foundation models"
    if any(k in text for k in ["agriculture", "ag-robotics", "crop", "food", "molecular farming"]):
        return "Agriculture & food systems"
    if any(k in text for k in ["silicon", "chip", "semiconductor", "edge", "foundation ai"]):
        return "AI chips & edge infrastructure"
    if any(k in text for k in ["manufacturing", "software-defined manufacturing", "factory", "mechatronics", "kinematics", "manipulation"]):
        return "Industrial robotics & automation"
    if any(k in text for k in ["aerospace", "defense", "drone", "aircraft", "microgravity", "space industries", "space-based", "ai pilots"]):
        return "Aerospace & defense autonomy"
    if any(k in text for k in ["chem", "life sci", "synthetic biology", "rna", "drug", "lab", "protein", "gen-bio", "bioreactor"]):
        return "AI labs, biology & chemistry"
    if any(k in text for k in ["auto", "spatial", "vision", "autonomous", "self-driving", "navigation", "ev physics"]):
        return "Autonomous mobility & spatial AI"
    if any(k in text for k in ["warehouse", "swarm", "logistics", "fulfillment"]):
        return "Warehouse & logistics robotics"
    if any(k in text for k in ["robotics", "mechanics"]):
        return "Industrial robotics & automation"
    return "General-purpose physical AI"


def company_regions_for_countries(countries: list[tuple[str, str]]) -> list[str]:
    regions = []
    for country, iso3 in countries:
        if iso3 == "USA":
            regions.append("US")
        elif iso3 == "CAN":
            regions.append("Canada")
        elif iso3 in EU_MEMBER_ISO3 or iso3 in {"GBR", "NOR", "CHE"}:
            regions.append("EU / Europe")
        elif iso3 in {"CHN", "IND", "JPN", "KOR", "TWN", "SGP"}:
            regions.append("China / Asia")
        elif iso3 in {"ARG", "BRA", "CHL", "MEX", "COL", "PER", "URY"}:
            regions.append("Latin America")
        else:
            regions.append("Other / mixed")
    return list(dict.fromkeys(regions)) or ["Other / mixed"]


def strategic_region_for_company(countries: list[tuple[str, str]]) -> str:
    regions = company_regions_for_countries(countries)
    if len(regions) == 1:
        return regions[0]
    return "Other / mixed"


def load_physical_ai_companies(path: str | Path = PHYSICAL_AI_COMPANIES_CSV) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def build_physical_ai_company_tables(
    companies_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    clean_cols = [
        "company_name",
        "country_raw",
        "country_list",
        "country_iso3_list",
        "strategic_region",
        "core_scientific_field",
        "company_subfield",
        "physical_ai_use",
        "active_status",
        "independence_status",
        "physical_ai_fit",
        "investment_low_usd_m",
        "investment_base_usd_m",
        "investment_high_usd_m",
        "investment_metric_type",
        "investment_confidence",
        "latest_round_or_event",
        "latest_round_or_event_year",
        "do_not_aggregate_without_metric_filter",
        "company_url",
        "source_urls",
        "status_notes",
        "is_multi_country",
        "company_count",
    ]
    summary_country_cols = [
        "country",
        "country_iso3",
        "active_company_exposures",
        "fractional_company_count",
        "investment_base_usd_m_fractional",
    ]
    summary_subfield_cols = [
        "company_subfield",
        "active_companies",
        "investment_low_usd_m",
        "investment_base_usd_m",
        "investment_high_usd_m",
        "top_regions",
        "metric_caution_rows",
    ]
    summary_region_cols = [
        "strategic_region",
        "active_companies",
        "investment_low_usd_m",
        "investment_base_usd_m",
        "investment_high_usd_m",
        "top_subfields",
        "metric_caution_rows",
    ]
    if companies_raw.empty:
        return (
            pd.DataFrame(columns=clean_cols),
            pd.DataFrame(columns=summary_country_cols),
            pd.DataFrame(columns=summary_subfield_cols),
            pd.DataFrame(columns=summary_region_cols),
        )

    active_mask = companies_raw["Active_Status"].map(clean_text).str.lower().str.contains("active", na=False)
    active_mask &= ~companies_raw["Active_Status"].map(clean_text).str.lower().str.contains("inactive", na=False)
    raw = companies_raw[active_mask].copy()
    rows = []
    country_rows = []
    for _, row in raw.iterrows():
        countries = split_company_countries(row.get("Country", ""))
        region = strategic_region_for_company(countries)
        subfield = classify_company_subfield(row)
        n_countries = max(len(countries), 1)
        funding_low = pd.to_numeric(row.get("Updated_Investment_USD_M_low"), errors="coerce")
        funding_base = pd.to_numeric(row.get("Updated_Investment_USD_M_base"), errors="coerce")
        funding_high = pd.to_numeric(row.get("Updated_Investment_USD_M_high"), errors="coerce")
        clean_row = {
            "company_name": clean_text(row.get("Updated_Name_or_Active_Label")) or clean_text(row.get("Startup Name")),
            "country_raw": clean_text(row.get("Country")),
            "country_list": "; ".join(country for country, _ in countries),
            "country_iso3_list": "; ".join(iso3 for _, iso3 in countries if iso3),
            "strategic_region": region,
            "core_scientific_field": clean_text(row.get("Core Scientific Field")),
            "company_subfield": subfield,
            "physical_ai_use": clean_text(row.get("How Physical Intelligence is Used")),
            "active_status": clean_text(row.get("Active_Status")),
            "independence_status": clean_text(row.get("Independence_Status")),
            "physical_ai_fit": clean_text(row.get("Physical_AI_Fit")),
            "investment_low_usd_m": funding_low,
            "investment_base_usd_m": funding_base,
            "investment_high_usd_m": funding_high,
            "investment_metric_type": clean_text(row.get("Investment_Metric_Type")),
            "investment_confidence": clean_text(row.get("Investment_Evidence_Confidence")),
            "latest_round_or_event": clean_text(row.get("Latest_Round_or_Event")),
            "latest_round_or_event_year": clean_text(row.get("Latest_Round_or_Event_Year")),
            "do_not_aggregate_without_metric_filter": clean_text(row.get("Do_Not_Aggregate_Without_Metric_Filter")),
            "company_url": clean_text(row.get("Updated_Website")) or clean_text(row.get("Website Link")),
            "source_urls": clean_text(row.get("Investment_Source_URLs")),
            "status_notes": clean_text(row.get("Status_Notes")),
            "is_multi_country": n_countries > 1,
            "company_count": 1.0,
        }
        rows.append(clean_row)
        for country, iso3 in countries:
            country_rows.append(
                {
                    "company_name": clean_row["company_name"],
                    "country": country,
                    "country_iso3": iso3,
                    "company_subfield": subfield,
                    "strategic_region": company_regions_for_countries([(country, iso3)])[0],
                    "active_company_exposure": 1.0,
                    "fractional_company_count": 1.0 / n_countries,
                    "investment_base_usd_m_fractional": funding_base / n_countries if pd.notna(funding_base) else np.nan,
                }
            )

    clean = pd.DataFrame(rows, columns=clean_cols)
    country_long = pd.DataFrame(country_rows)
    if country_long.empty:
        country_summary = pd.DataFrame(columns=summary_country_cols)
    else:
        country_summary = (
            country_long.groupby(["country", "country_iso3"], dropna=False)
            .agg(
                active_company_exposures=("active_company_exposure", "sum"),
                fractional_company_count=("fractional_company_count", "sum"),
                investment_base_usd_m_fractional=("investment_base_usd_m_fractional", "sum"),
            )
            .reset_index()[summary_country_cols]
            .sort_values(["active_company_exposures", "investment_base_usd_m_fractional"], ascending=False)
        )

    caution = clean["do_not_aggregate_without_metric_filter"].map(clean_text).ne("")
    subfield_summary = (
        clean.assign(metric_caution_row=caution)
        .groupby("company_subfield", dropna=False)
        .agg(
            active_companies=("company_name", "nunique"),
            investment_low_usd_m=("investment_low_usd_m", "sum"),
            investment_base_usd_m=("investment_base_usd_m", "sum"),
            investment_high_usd_m=("investment_high_usd_m", "sum"),
            top_regions=("strategic_region", _join_top),
            metric_caution_rows=("metric_caution_row", "sum"),
        )
        .reset_index()[summary_subfield_cols]
        .sort_values(["active_companies", "investment_base_usd_m"], ascending=False)
    )

    region_order = ["US", "EU / Europe", "China / Asia", "Canada", "Latin America", "Other / mixed"]
    region_summary = (
        clean.assign(metric_caution_row=caution)
        .groupby("strategic_region", dropna=False)
        .agg(
            active_companies=("company_name", "nunique"),
            investment_low_usd_m=("investment_low_usd_m", "sum"),
            investment_base_usd_m=("investment_base_usd_m", "sum"),
            investment_high_usd_m=("investment_high_usd_m", "sum"),
            top_subfields=("company_subfield", _join_top),
            metric_caution_rows=("metric_caution_row", "sum"),
        )
        .reindex(region_order, fill_value=0)
        .rename_axis("strategic_region")
        .reset_index()[summary_region_cols]
    )
    return clean, country_summary, subfield_summary, region_summary


def make_quality_checks(cleaned: pd.DataFrame, origin_long: pd.DataFrame) -> dict[str, pd.DataFrame | int]:
    checks: dict[str, pd.DataFrame | int] = {}
    checks["missing_doi_or_link"] = cleaned[cleaned["doi_or_link_clean"].eq("")]
    checks["missing_year"] = cleaned[cleaned["year_int"].isna()]
    checks["duplicate_id"] = cleaned[cleaned["paper_id"].duplicated(keep=False)]
    checks["ambiguous_country"] = origin_long[
        origin_long["origin_country_iso3"].eq("") | origin_long["origin_country_normalization_failed"]
    ]
    checks["empty_institution"] = cleaned[cleaned["institution_clean"].eq("")]
    checks["empty_rationale"] = cleaned[cleaned["Billionaire_rationale"].map(clean_text).eq("")]
    return checks


def choose_template_for_paper(field: str, broad_area: str) -> str:
    text = f"{field} {broad_area}".lower()
    if any(k in text for k in ["vaccine", "pharma", "drug", "immunotherapy", "therapy", "biotech", "mrna", "pcr"]):
        return "pharma_biotech_vaccines"
    if any(k in text for k in ["battery", "semiconductor", "hardware", "materials", "display", "led", "photoresist", "finfet"]):
        return "batteries_materials_semiconductors_hardware"
    if any(k in text for k in ["ai", "cloud", "software", "internet", "search", "transformer", "lstm", "robot", "blockchain"]):
        return "software_ai_cloud_internet_platforms"
    if any(k in text for k in ["cryptography", "ethernet", "wireless", "mimo", "coding", "protocol", "network"]):
        return "communications_standards_cryptography_protocols"
    if any(k in text for k in ["crop", "plant", "agricultur", "seed"]):
        return "agriculture_crop_biotechnology"
    if any(k in text for k in ["robot", "slam", "automation", "autonomous"]):
        return "robotics_industrial_automation"
    return "software_ai_cloud_internet_platforms"


def example_beneficiaries_for_paper(row: pd.Series) -> list[tuple[str, str]]:
    field = clean_text(row["Field_or_platform"]).lower()
    paper = clean_text(row["Paper_or_discovery"]).lower()
    combined = f"{field} {paper}"
    if "lithium" in combined or "battery" in combined:
        return [
            ("Japan", "commercialization"),
            ("South Korea", "manufacturing"),
            ("China", "manufacturing"),
            ("United States", "company_headquarters"),
            ("Germany", "adoption_market"),
            (row["origin_country_primary"], "research_origin"),
        ]
    if "transformer" in combined or "bert" in combined or "alexnet" in combined or "resnet" in combined:
        return [
            ("United States", "company_headquarters"),
            ("Taiwan", "manufacturing"),
            ("Netherlands", "equipment_supplier"),
            ("South Korea", "supply_chain"),
            ("China", "adoption_market"),
            (row["origin_country_primary"], "research_origin"),
        ]
    if "mrna" in combined or "nucleoside" in combined:
        return [
            ("United States", "company_headquarters"),
            ("Germany", "company_headquarters"),
            ("Belgium", "manufacturing"),
            ("Switzerland", "supply_chain"),
            (row["origin_country_primary"], "research_origin"),
        ]
    if "pcr" in combined or "beta-globin" in combined:
        return [
            ("United States", "company_headquarters"),
            ("Switzerland", "company_headquarters"),
            ("Germany", "equipment_supplier"),
            ("Japan", "manufacturing"),
            ("China", "adoption_market"),
            ("United Kingdom", "adoption_market"),
        ]
    return []


def create_assumptions_template(cleaned: pd.DataFrame) -> pd.DataFrame:
    rows = []
    last_updated = date.today().isoformat()
    example_ids = set()
    for _, row in cleaned.iterrows():
        beneficiaries = example_beneficiaries_for_paper(row)
        if beneficiaries:
            example_ids.add(int(row["paper_id"]))
        for country, role in beneficiaries:
            country_name, iso3 = normalize_country_name(country)
            template_name = choose_template_for_paper(row["Field_or_platform"], row["Broad_area"])
            weights = ROLE_WEIGHT_TEMPLATES[template_name]
            role_key = role
            share = weights.get(role_key, weights.get("research_origin", 0.10))
            rows.append(
                {
                    "paper_id": int(row["paper_id"]),
                    "paper_or_discovery": row["Paper_or_discovery"],
                    "field_or_platform": row["Field_or_platform"],
                    "beneficiary_country": country_name,
                    "beneficiary_country_iso3": iso3,
                    "beneficiary_role": role,
                    "enabled_revenue_low_usd": np.nan,
                    "enabled_revenue_base_usd": np.nan,
                    "enabled_revenue_high_usd": np.nan,
                    "paper_attribution_low": np.nan,
                    "paper_attribution_base": np.nan,
                    "paper_attribution_high": np.nan,
                    "country_capture_share_low": share,
                    "country_capture_share_base": share,
                    "country_capture_share_high": share,
                    "role_margin_low": np.nan,
                    "role_margin_base": np.nan,
                    "role_margin_high": np.nan,
                    "benefit_type": "gross_revenue_capture",
                    "confidence_level": "example_not_audited",
                    "evidence_summary": "Example structure only. Fill enabled revenue, attribution, shares, margins, and audited evidence before using estimates.",
                    "source_1": row["DOI_or_link"],
                    "source_2": "",
                    "source_3": "",
                    "analyst_notes": f"Model-based starter row using {template_name} role-weight defaults; monetary estimates intentionally blank.",
                    "last_updated": last_updated,
                }
            )
    assumptions = pd.DataFrame(rows, columns=ASSUMPTION_COLUMNS)
    if assumptions.empty:
        assumptions = pd.DataFrame(columns=ASSUMPTION_COLUMNS)
    for scenario in ["low", "base", "high"]:
        share_col = f"country_capture_share_{scenario}"
        assumptions = normalize_country_shares(assumptions, share_col)
    return assumptions


def validate_assumptions(assumptions_df: pd.DataFrame) -> pd.DataFrame:
    """Check required columns, missing sources, numeric ranges, and share sums."""
    warnings = []
    missing_cols = [c for c in ASSUMPTION_COLUMNS if c not in assumptions_df.columns]
    if missing_cols:
        warnings.append({"severity": "error", "check": "missing_columns", "detail": ", ".join(missing_cols)})
        return pd.DataFrame(warnings)

    if assumptions_df.empty:
        warnings.append({"severity": "warning", "check": "empty_assumptions", "detail": "No benefit assumptions provided."})
        return pd.DataFrame(warnings)

    bad_roles = sorted(set(assumptions_df["beneficiary_role"].dropna()) - set(ALLOWED_ROLES))
    if bad_roles:
        warnings.append({"severity": "warning", "check": "unknown_beneficiary_role", "detail": ", ".join(bad_roles)})

    bad_benefit_types = sorted(set(assumptions_df["benefit_type"].dropna()) - set(ALLOWED_BENEFIT_TYPES))
    if bad_benefit_types:
        warnings.append({"severity": "warning", "check": "unknown_benefit_type", "detail": ", ".join(bad_benefit_types)})

    source_cols = ["source_1", "source_2", "source_3"]
    missing_sources = assumptions_df[source_cols].fillna("").apply(lambda s: not any(clean_text(v) for v in s), axis=1)
    if missing_sources.any():
        warnings.append(
            {
                "severity": "warning",
                "check": "missing_sources",
                "detail": f"{int(missing_sources.sum())} assumption rows have no source.",
            }
        )

    numeric_range_cols = [
        "paper_attribution_low",
        "paper_attribution_base",
        "paper_attribution_high",
        "country_capture_share_low",
        "country_capture_share_base",
        "country_capture_share_high",
        "role_margin_low",
        "role_margin_base",
        "role_margin_high",
    ]
    for col in numeric_range_cols:
        vals = pd.to_numeric(assumptions_df[col], errors="coerce")
        bad = vals.notna() & ((vals < 0) | (vals > 1))
        if bad.any():
            warnings.append({"severity": "warning", "check": f"{col}_outside_0_1", "detail": f"{int(bad.sum())} rows"})

    for scenario in ["low", "base", "high"]:
        col = f"country_capture_share_{scenario}"
        complete_for_scenario = (
            pd.to_numeric(assumptions_df[f"enabled_revenue_{scenario}_usd"], errors="coerce").notna()
            & pd.to_numeric(assumptions_df[f"paper_attribution_{scenario}"], errors="coerce").notna()
        )
        if not complete_for_scenario.any():
            continue
        complete_assumptions = assumptions_df[complete_for_scenario]
        sums = pd.to_numeric(complete_assumptions[col], errors="coerce").groupby(complete_assumptions["paper_id"]).sum(min_count=1)
        bad = sums[sums.notna() & ~np.isclose(sums, 1.0, atol=0.01)]
        if not bad.empty:
            detail = "; ".join(f"paper {paper_id}: {value:.3f}" for paper_id, value in bad.items())
            warnings.append({"severity": "warning", "check": f"{scenario}_shares_not_sum_1", "detail": detail})

    attr_vals = pd.to_numeric(assumptions_df["paper_attribution_base"], errors="coerce")
    high_attr = attr_vals.notna() & (attr_vals > 0.50)
    if high_attr.any():
        warnings.append(
            {
                "severity": "warning",
                "check": "unusually_high_attribution",
                "detail": f"{int(high_attr.sum())} rows have base attribution above 0.50.",
            }
        )
    return pd.DataFrame(warnings, columns=["severity", "check", "detail"])


def normalize_country_shares(assumptions_df: pd.DataFrame, share_col: str) -> pd.DataFrame:
    """Normalize country capture shares within each paper and scenario."""
    df = assumptions_df.copy()
    if df.empty or share_col not in df.columns:
        return df
    values = pd.to_numeric(df[share_col], errors="coerce")
    sums = values.groupby(df["paper_id"]).transform("sum")
    mask = values.notna() & sums.notna() & (sums > 0)
    df.loc[mask, share_col] = values[mask] / sums[mask]
    return df


def calculate_country_benefit(assumptions_df: pd.DataFrame, cleaned: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate low/base/high revenue capture and profit proxy."""
    if assumptions_df.empty:
        estimates = pd.DataFrame(
            columns=[
                "paper_id",
                "paper_or_discovery",
                "field_or_platform",
                "origin_country_list",
                "beneficiary_country",
                "beneficiary_country_iso3",
                "beneficiary_role",
                "revenue_capture_low_usd",
                "revenue_capture_base_usd",
                "revenue_capture_high_usd",
                "profit_proxy_low_usd",
                "profit_proxy_base_usd",
                "profit_proxy_high_usd",
                "confidence_level",
                "evidence_summary",
                "sources",
                "analyst_notes",
            ]
        )
        long = pd.DataFrame(columns=["paper_id", "scenario", "metric", "value_usd"])
        return estimates, long

    df = assumptions_df.copy()
    for scenario in ["low", "base", "high"]:
        for col in [
            f"enabled_revenue_{scenario}_usd",
            f"paper_attribution_{scenario}",
            f"country_capture_share_{scenario}",
            f"role_margin_{scenario}",
        ]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        revenue_col = f"revenue_capture_{scenario}_usd"
        profit_col = f"profit_proxy_{scenario}_usd"
        df[revenue_col] = (
            df[f"enabled_revenue_{scenario}_usd"]
            * df[f"paper_attribution_{scenario}"]
            * df[f"country_capture_share_{scenario}"]
        )
        df[profit_col] = df[revenue_col] * df[f"role_margin_{scenario}"]

    origin_lookup = cleaned.set_index("paper_id")["origin_country_list"].to_dict()
    broad_lookup = cleaned.set_index("paper_id")["broad_area_clean"].to_dict()
    confidence_lookup = cleaned.set_index("paper_id")["confidence_tier_clean"].to_dict()
    df["origin_country_list"] = df["paper_id"].map(origin_lookup).fillna("")
    df["broad_area_clean"] = df["paper_id"].map(broad_lookup).fillna("")
    df["paper_confidence_tier"] = df["paper_id"].map(confidence_lookup).fillna("")
    df["sources"] = df[["source_1", "source_2", "source_3"]].fillna("").agg(
        lambda s: "; ".join([clean_text(v) for v in s if clean_text(v)]), axis=1
    )

    estimates = df[
        [
            "paper_id",
            "paper_or_discovery",
            "field_or_platform",
            "origin_country_list",
            "beneficiary_country",
            "beneficiary_country_iso3",
            "beneficiary_role",
            "revenue_capture_low_usd",
            "revenue_capture_base_usd",
            "revenue_capture_high_usd",
            "profit_proxy_low_usd",
            "profit_proxy_base_usd",
            "profit_proxy_high_usd",
            "confidence_level",
            "evidence_summary",
            "sources",
            "analyst_notes",
        ]
    ].copy()

    long_rows = []
    id_cols = [
        "paper_id",
        "paper_or_discovery",
        "field_or_platform",
        "origin_country_list",
        "beneficiary_country",
        "beneficiary_country_iso3",
        "beneficiary_role",
        "confidence_level",
        "broad_area_clean",
        "paper_confidence_tier",
    ]
    for _, row in df.iterrows():
        base = {col: row[col] for col in id_cols}
        for scenario in ["low", "base", "high"]:
            for metric, col in [
                ("revenue_capture", f"revenue_capture_{scenario}_usd"),
                ("profit_proxy", f"profit_proxy_{scenario}_usd"),
            ]:
                long_row = base.copy()
                long_row.update({"scenario": scenario, "metric": metric, "value_usd": row[col]})
                long_rows.append(long_row)
    benefit_long = pd.DataFrame(long_rows)
    return estimates, benefit_long


def _join_top(values: pd.Series, limit: int = 3) -> str:
    clean = [clean_text(v) for v in values.dropna() if clean_text(v)]
    if not clean:
        return ""
    counts = pd.Series(clean).value_counts()
    return "; ".join(counts.head(limit).index.tolist())


def aggregate_country_summary(
    benefit_estimates: pd.DataFrame, cleaned: pd.DataFrame, origin_long: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate by country, role, broad area, and confidence tier."""
    cols = [
        "beneficiary_country",
        "beneficiary_country_iso3",
        "revenue_capture_low_usd",
        "revenue_capture_base_usd",
        "revenue_capture_high_usd",
        "profit_proxy_low_usd",
        "profit_proxy_base_usd",
        "profit_proxy_high_usd",
        "number_of_originated_papers",
        "number_of_benefited_papers",
        "top_beneficiary_roles",
        "top_fields",
        "confidence_mix",
        "originated_paper_share",
        "estimated_value_captured_share",
        "origin_to_capture_gap",
    ]
    if benefit_estimates.empty:
        return pd.DataFrame(columns=cols)

    df = benefit_estimates.copy()
    numeric_cols = [
        "revenue_capture_low_usd",
        "revenue_capture_base_usd",
        "revenue_capture_high_usd",
        "profit_proxy_low_usd",
        "profit_proxy_base_usd",
        "profit_proxy_high_usd",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    grouped = df.groupby(["beneficiary_country", "beneficiary_country_iso3"], dropna=False)
    summary = grouped[numeric_cols].sum(min_count=1).reset_index()
    summary["number_of_benefited_papers"] = grouped["paper_id"].nunique().values
    summary["top_beneficiary_roles"] = grouped["beneficiary_role"].agg(_join_top).values
    summary["top_fields"] = grouped["field_or_platform"].agg(_join_top).values
    summary["confidence_mix"] = grouped["confidence_level"].agg(_join_top).values

    originated_counts = (
        origin_long[origin_long["origin_country"].ne("")]
        .groupby("origin_country")["paper_id"]
        .nunique()
        .rename("number_of_originated_papers")
    )
    summary["number_of_originated_papers"] = summary["beneficiary_country"].map(originated_counts).fillna(0).astype(int)

    total_originated_records = max(float(originated_counts.sum()), 1.0)
    summary["originated_paper_share"] = summary["number_of_originated_papers"] / total_originated_records
    total_value = summary["revenue_capture_base_usd"].sum(skipna=True)
    if pd.notna(total_value) and total_value > 0:
        summary["estimated_value_captured_share"] = summary["revenue_capture_base_usd"] / total_value
    else:
        summary["estimated_value_captured_share"] = np.nan
    summary["origin_to_capture_gap"] = summary["estimated_value_captured_share"] - summary["originated_paper_share"]

    return summary[cols].sort_values(
        ["revenue_capture_base_usd", "number_of_benefited_papers"], ascending=[False, False], na_position="last"
    )


def build_origin_country_summary(origin_long: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    if origin_long.empty:
        return pd.DataFrame()
    base = origin_long[origin_long["origin_country"].map(clean_text).ne("")].copy()
    if base.empty:
        return pd.DataFrame()
    grouped = base.groupby(["origin_country", "origin_country_iso3"], dropna=False)
    summary = grouped.agg(
        originated_papers=("paper_id", "nunique"),
        first_year=("year_int", "min"),
        latest_year=("year_int", "max"),
        top_broad_areas=("broad_area_clean", _join_top),
        top_fields=("field_clean", _join_top),
    ).reset_index()
    public_lookup = cleaned.set_index("paper_id")["public_private_clean"].to_dict()
    base["public_private_clean"] = base["paper_id"].map(public_lookup).fillna("")
    summary["public_private_mix"] = grouped["paper_id"].apply(
        lambda ids: _join_top(pd.Series([public_lookup.get(pid, "") for pid in ids]))
    ).values
    total = max(float(summary["originated_papers"].sum()), 1.0)
    summary["originated_paper_share"] = summary["originated_papers"] / total
    return summary.sort_values("originated_papers", ascending=False)


def build_origin_to_beneficiary_flow(china_update: pd.DataFrame, origin_long: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "paper_id",
        "paper_or_discovery",
        "field_or_platform",
        "origin_country",
        "origin_country_iso3",
        "beneficiary_country",
        "beneficiary_country_iso3",
        "beneficiary_role",
        "value_capture_channel",
        "scenario",
        "enabled_market_revenue_usd",
        "paper_attribution_factor",
        "country_capture_share",
        "country_revenue_capture_usd",
        "role_margin",
        "country_profit_proxy_usd",
        "value_type",
        "estimate_basis",
        "confidence",
        "evidence_urls",
        "notes",
        "assumption_status",
        "partial_country_benefit_layer",
    ]
    if china_update.empty:
        return pd.DataFrame(columns=columns)
    origin_by_paper = (
        origin_long[origin_long["origin_country"].map(clean_text).ne("")]
        .groupby("paper_id")
        .agg(
            origin_country=("origin_country", lambda s: "; ".join(dict.fromkeys(s.astype(str)))),
            origin_country_iso3=("origin_country_iso3", lambda s: "; ".join([v for v in dict.fromkeys(s.astype(str)) if v])),
        )
        .reset_index()
    )
    origin_lookup = origin_by_paper.set_index("paper_id").to_dict("index")
    rows = []
    for _, row in china_update.iterrows():
        paper_id = int(row["paper_id"])
        origin = origin_lookup.get(
            paper_id,
            {"origin_country": clean_text(row["Origin_country_or_countries"]), "origin_country_iso3": ""},
        )
        for scenario in ["low", "base", "high"]:
            rows.append(
                {
                    "paper_id": paper_id,
                    "paper_or_discovery": row["Paper_or_discovery"],
                    "field_or_platform": row["Field_or_platform"],
                    "origin_country": origin["origin_country"],
                    "origin_country_iso3": origin["origin_country_iso3"],
                    "beneficiary_country": "China",
                    "beneficiary_country_iso3": "CHN",
                    "beneficiary_role": row["beneficiary_role_canonical"],
                    "value_capture_channel": row["Value_capture_channels"],
                    "scenario": scenario,
                    "enabled_market_revenue_usd": np.nan,
                    "paper_attribution_factor": np.nan,
                    "country_capture_share": row[f"china_capture_share_{scenario}"],
                    "country_revenue_capture_usd": np.nan,
                    "role_margin": np.nan,
                    "country_profit_proxy_usd": np.nan,
                    "value_type": "value_added",
                    "estimate_basis": row["Estimate_basis"],
                    "confidence": row["Benefit_confidence"],
                    "evidence_urls": row["Evidence_urls"],
                    "notes": row["Value_capture_notes"],
                    "assumption_status": row["Assumption_status"],
                    "partial_country_benefit_layer": True,
                }
            )
    return pd.DataFrame(rows, columns=columns)


def build_field_country_summary(flow_df: pd.DataFrame) -> pd.DataFrame:
    if flow_df.empty:
        return pd.DataFrame(
            columns=[
                "field_or_platform",
                "beneficiary_country",
                "scenario",
                "papers",
                "average_capture_share",
                "median_capture_share",
                "max_capture_share",
                "roles",
                "partial_country_benefit_layer",
            ]
        )
    grouped = flow_df.groupby(["field_or_platform", "beneficiary_country", "scenario"], dropna=False)
    summary = grouped.agg(
        papers=("paper_id", "nunique"),
        average_capture_share=("country_capture_share", "mean"),
        median_capture_share=("country_capture_share", "median"),
        max_capture_share=("country_capture_share", "max"),
        roles=("beneficiary_role", _join_top),
        partial_country_benefit_layer=("partial_country_benefit_layer", "max"),
    ).reset_index()
    return summary.sort_values(["scenario", "average_capture_share"], ascending=[True, False])


def build_public_private_spillover_summary(flow_df: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "public_private_origin",
        "beneficiary_country",
        "beneficiary_role",
        "scenario",
        "papers",
        "average_capture_share",
        "median_capture_share",
        "partial_country_benefit_layer",
    ]
    if flow_df.empty:
        return pd.DataFrame(columns=columns)
    lookup = cleaned.set_index("paper_id")["public_private_clean"].to_dict()
    df = flow_df.copy()
    df["public_private_origin"] = df["paper_id"].map(lookup).fillna("Unknown")
    grouped = df.groupby(["public_private_origin", "beneficiary_country", "beneficiary_role", "scenario"], dropna=False)
    return grouped.agg(
        papers=("paper_id", "nunique"),
        average_capture_share=("country_capture_share", "mean"),
        median_capture_share=("country_capture_share", "median"),
        partial_country_benefit_layer=("partial_country_benefit_layer", "max"),
    ).reset_index()[columns]


def build_quality_check_report(
    quality_checks: dict[str, pd.DataFrame | int],
    assumption_warnings: pd.DataFrame,
    cleaned: pd.DataFrame,
    china_update: pd.DataFrame,
    flow_df: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    def add_check(check: str, severity: str, count: int, detail: str) -> None:
        rows.append({"check": check, "severity": severity, "count": int(count), "detail": detail})

    for key, value in quality_checks.items():
        count = len(value) if isinstance(value, pd.DataFrame) else int(value)
        severity = "warning" if count else "ok"
        add_check(key, severity, count, f"{count} rows flagged.")

    if not assumption_warnings.empty:
        for _, row in assumption_warnings.iterrows():
            add_check(clean_text(row["check"]), clean_text(row["severity"]) or "warning", 1, clean_text(row["detail"]))
    else:
        add_check("assumption_validation", "ok", 0, "No assumption validation warnings.")

    if not china_update.empty:
        present_ids = set(pd.to_numeric(china_update["paper_id"], errors="coerce").dropna().astype(int))
        missing_expected = sorted(EXPECTED_CHINA_BENEFICIARY_IDS - present_ids)
        add_check(
            "china_expected_v020_ids_present",
            "warning" if missing_expected else "ok",
            len(missing_expected),
            "Missing expected China beneficiary paper IDs: " + ", ".join(map(str, missing_expected))
            if missing_expected
            else "All expected v0.2.0 China beneficiary paper IDs are present.",
        )
        missing_role = china_update["beneficiary_role_canonical"].map(clean_text).eq("")
        missing_share = china_update[
            ["china_capture_share_low", "china_capture_share_base", "china_capture_share_high"]
        ].isna().any(axis=1)
        missing_confidence = china_update["Benefit_confidence"].map(clean_text).eq("")
        missing_notes = china_update["Value_capture_notes"].map(clean_text).eq("")
        add_check(
            "china_flagged_rows_missing_required_fields",
            "warning" if (missing_role | missing_share | missing_confidence | missing_notes).any() else "ok",
            int((missing_role | missing_share | missing_confidence | missing_notes).sum()),
            "China beneficiary rows should include role, low/base/high shares, confidence, and notes.",
        )
        add_check(
            "partial_china_layer_not_complete_global_allocation",
            "info",
            len(china_update),
            "China v0.2.0 rows are a partial beneficiary layer and should not be treated as a full country ranking.",
        )
    else:
        add_check("china_update_missing", "warning", 1, f"{CHINA_BENEFIT_LONG_CSV} not found or empty.")

    if not flow_df.empty:
        bad_share = pd.to_numeric(flow_df["country_capture_share"], errors="coerce").pipe(lambda s: s.notna() & ((s < 0) | (s > 1)))
        add_check(
            "flow_capture_share_outside_0_1",
            "warning" if bad_share.any() else "ok",
            int(bad_share.sum()),
            "Country capture shares should be fractions between 0 and 1.",
        )

    negative_cols = [
        col
        for col in cleaned.columns
        if col.endswith("_usd") and pd.api.types.is_numeric_dtype(cleaned[col])
    ]
    negative_count = int(sum((cleaned[col] < 0).sum() for col in negative_cols)) if negative_cols else 0
    add_check(
        "negative_revenue_or_profit_values",
        "warning" if negative_count else "ok",
        negative_count,
        "Negative monetary values require explicit cost/loss labeling.",
    )
    return pd.DataFrame(rows, columns=["check", "severity", "count", "detail"])


def make_figures(
    cleaned: pd.DataFrame,
    origin_long: pd.DataFrame,
    benefit_estimates: pd.DataFrame,
    country_summary: pd.DataFrame,
    china_update: pd.DataFrame | None = None,
    flow_df: pd.DataFrame | None = None,
    public_private_spillover: pd.DataFrame | None = None,
    physical_intelligence_links: pd.DataFrame | None = None,
    physical_intelligence_domain_summary: pd.DataFrame | None = None,
    physical_ai_company_country_summary: pd.DataFrame | None = None,
    physical_ai_company_subfield_summary: pd.DataFrame | None = None,
    physical_ai_company_region_summary: pd.DataFrame | None = None,
):
    template = "plotly_white"
    figures: dict[str, go.Figure] = {}

    year_counts = cleaned.dropna(subset=["year_int"]).groupby("year_int").size().reset_index(name="papers")
    figures["papers_by_year"] = px.bar(
        year_counts,
        x="year_int",
        y="papers",
        template=template,
        labels={"year_int": "Publication year", "papers": "Papers"},
        title="Papers by publication year",
    )
    figures["papers_by_year"].update_traces(marker_color=DESIGN_COLORS["origin"])

    decade_counts = cleaned.groupby("decade").size().reset_index(name="papers")
    decade_counts = decade_counts[decade_counts["decade"].ne("")]
    figures["papers_by_decade"] = px.bar(
        decade_counts,
        x="decade",
        y="papers",
        template=template,
        labels={"decade": "Decade", "papers": "Papers"},
        title="Papers by decade",
    )
    figures["papers_by_decade"].update_traces(marker_color=DESIGN_COLORS["origin"])

    area_counts = cleaned["broad_area_clean"].value_counts().reset_index()
    area_counts.columns = ["broad_area", "papers"]
    figures["broad_area"] = px.bar(
        area_counts.head(20),
        x="papers",
        y="broad_area",
        orientation="h",
        template=template,
        labels={"papers": "Papers", "broad_area": "Broad area"},
        title="Papers by broad area",
    )
    figures["broad_area"].update_traces(marker_color=DESIGN_COLORS["origin"])
    figures["broad_area"].update_layout(yaxis={"categoryorder": "total ascending"})

    origin_counts = (
        origin_long[origin_long["origin_country"].ne("")]
        .groupby(["origin_country", "origin_country_iso3"])["paper_id"]
        .nunique()
        .reset_index(name="papers")
        .sort_values("papers", ascending=False)
    )
    figures["origin_country_bar"] = px.bar(
        origin_counts.head(20),
        x="papers",
        y="origin_country",
        orientation="h",
        template=template,
        labels={"papers": "Originated papers", "origin_country": "Country"},
        title="Research-origin countries",
    )
    figures["origin_country_bar"].update_traces(marker_color=DESIGN_COLORS["origin"])
    figures["origin_country_bar"].update_layout(yaxis={"categoryorder": "total ascending"})

    origin_map = origin_counts[origin_counts["origin_country_iso3"].ne("")]
    figures["origin_country_map"] = px.choropleth(
        origin_map,
        locations="origin_country_iso3",
        color="papers",
        hover_name="origin_country",
        color_continuous_scale="Viridis",
        template=template,
        labels={"papers": "Originated papers"},
        title="Research-origin country map",
    )
    figures["origin_country_map"].update_geos(showframe=False, showcoastlines=True)

    pp_counts = cleaned["public_private_clean"].replace("", "Unknown").value_counts().reset_index()
    pp_counts.columns = ["public_private", "papers"]
    pp_order = ["Public", "Private", "Mixed", "Non-institutional", "Unknown"]
    pp_counts["sort_order"] = pp_counts["public_private"].map({value: i for i, value in enumerate(pp_order)}).fillna(99)
    pp_counts = pp_counts.sort_values(["sort_order", "public_private"])
    figures["public_private"] = px.pie(
        pp_counts,
        values="papers",
        names="public_private",
        hole=0.45,
        template=template,
        color="public_private",
        color_discrete_map={
            "Public": DESIGN_COLORS["public_origin"],
            "Private": DESIGN_COLORS["private_origin"],
            "Mixed": DESIGN_COLORS["mixed_origin"],
            "Non-institutional": "#64748b",
        },
        title="Research-origin institution type",
    )
    figures["public_private"].update_traces(
        textinfo="label+value+percent",
        textposition="outside",
        hovertemplate="%{label}: %{value} papers (%{percent})<extra></extra>",
    )
    figures["public_private"].update_layout(
        legend_title_text="Institution type",
        uniformtext_minsize=12,
        uniformtext_mode="hide",
    )

    if physical_intelligence_links is not None and not physical_intelligence_links.empty:
        pi_links = physical_intelligence_links.copy()
        relevance_labels = {
            "Direct physical-intelligence substrate": "Direct substrate",
            "Enabling digital infrastructure": "Digital infrastructure",
            "Adjacent economic platform": "Adjacent platform",
        }
        relevance_colors = {
            "Direct substrate": DESIGN_COLORS["success"],
            "Digital infrastructure": DESIGN_COLORS["origin"],
            "Adjacent platform": DESIGN_COLORS["warning"],
        }
        capability_counts = (
            pi_links.drop_duplicates(["paper_id", "pi_capability", "pi_relevance"])
            .groupby(["pi_capability", "pi_relevance"], dropna=False)["paper_id"]
            .nunique()
            .reset_index(name="papers")
            .sort_values("papers", ascending=False)
        )
        capability_counts["relevance_label"] = capability_counts["pi_relevance"].map(relevance_labels).fillna(
            capability_counts["pi_relevance"]
        )
        figures["physical_intelligence_capabilities"] = px.bar(
            capability_counts,
            x="papers",
            y="pi_capability",
            color="relevance_label",
            orientation="h",
            template=template,
            color_discrete_map=relevance_colors,
            labels={
                "papers": "Linked papers",
                "pi_capability": "",
                "relevance_label": "Relevance",
            },
            title="Paper-linked capabilities for Physical Intelligence",
        )
        figures["physical_intelligence_capabilities"].update_layout(
            barmode="stack",
            height=450,
            margin=dict(l=178, r=26, t=78, b=104),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.22,
                xanchor="left",
                x=0,
                title_text="",
            ),
            yaxis=dict(title=None, categoryorder="total ascending", automargin=True),
            xaxis=dict(title="Linked papers", rangemode="tozero", zeroline=True),
        )

        sankey_input = pi_links.drop_duplicates(
            ["paper_id", "pi_platform_family", "pi_capability", "science_acceleration_domain"]
        ).copy()
        figures["physical_intelligence_sankey"] = make_sankey(
            sankey_input,
            ["pi_platform_family", "pi_capability", "science_acceleration_domain"],
            "Platform families -> Physical Intelligence capabilities -> science domains",
        )

    if (
        physical_intelligence_domain_summary is not None
        and not physical_intelligence_domain_summary.empty
    ):
        domain_df = physical_intelligence_domain_summary.sort_values("papers", ascending=True)
        figures["physical_intelligence_domains"] = px.bar(
            domain_df,
            x="papers",
            y="science_acceleration_domain",
            orientation="h",
            template=template,
            text="papers",
            labels={
                "papers": "Linked papers",
                "science_acceleration_domain": "",
            },
            title="Science domains linked to platform base",
        )
        domain_max = float(domain_df["papers"].max()) if not domain_df.empty else 1.0
        figures["physical_intelligence_domains"].update_traces(
            marker_color=DESIGN_COLORS["value_capture"],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color=DESIGN_COLORS["ink"]),
            cliponaxis=False,
        )
        figures["physical_intelligence_domains"].update_layout(
            height=450,
            margin=dict(l=190, r=24, t=82, b=58),
            showlegend=False,
            yaxis=dict(
                title=None,
                categoryorder="array",
                categoryarray=domain_df["science_acceleration_domain"].tolist(),
                automargin=True,
            ),
            xaxis=dict(title="Linked papers", range=[0, max(domain_max * 1.08, domain_max + 1)]),
        )

    if physical_ai_company_country_summary is not None and not physical_ai_company_country_summary.empty:
        country_df = physical_ai_company_country_summary.copy().head(16)
        country_df["count_label"] = country_df["active_company_exposures"].map(lambda value: f"{float(value):.0f}")
        figures["physical_ai_country_counts"] = px.bar(
            country_df.sort_values("active_company_exposures", ascending=True),
            x="active_company_exposures",
            y="country",
            orientation="h",
            text="count_label",
            template=template,
            labels={"active_company_exposures": "Active company-country exposures", "country": ""},
            title="Active Physical AI companies by country",
            hover_data={
                "fractional_company_count": ":.1f",
                "investment_base_usd_m_fractional": ":,.0f",
                "count_label": False,
            },
        )
        figures["physical_ai_country_counts"].update_traces(
            marker_color=DESIGN_COLORS["mixed_origin"],
            textposition="outside",
            textfont=dict(color=DESIGN_COLORS["ink"]),
            cliponaxis=False,
        )
        country_max = max(float(country_df["active_company_exposures"].max()), 1.0)
        figures["physical_ai_country_counts"].update_layout(
            height=460,
            margin=dict(l=132, r=42, t=72, b=46),
            showlegend=False,
            yaxis=dict(title=None, automargin=True),
            xaxis=dict(title=None, range=[0, country_max * 1.16]),
        )

    if physical_ai_company_subfield_summary is not None and not physical_ai_company_subfield_summary.empty:
        subfield_df = physical_ai_company_subfield_summary.copy()
        subfield_df["funding_base_usd_b"] = subfield_df["investment_base_usd_m"] / 1000.0
        subfield_df["funding_low_usd_b"] = subfield_df["investment_low_usd_m"] / 1000.0
        subfield_df["funding_high_usd_b"] = subfield_df["investment_high_usd_m"] / 1000.0
        subfield_df["count_label"] = subfield_df["active_companies"].map(lambda value: f"{int(value)}")
        subfield_df["funding_label"] = subfield_df["funding_base_usd_b"].map(lambda value: f"${value:.1f}B")

        subfield_count_plot = subfield_df.sort_values("active_companies", ascending=True)
        figures["physical_ai_subfield_counts"] = px.bar(
            subfield_count_plot,
            x="active_companies",
            y="company_subfield",
            orientation="h",
            text="count_label",
            template=template,
            labels={"active_companies": "Active companies", "company_subfield": ""},
            title="Active companies by Physical AI sub-field",
        )
        figures["physical_ai_subfield_counts"].update_traces(
            marker_color=DESIGN_COLORS["success"],
            textposition="outside",
            textfont=dict(color=DESIGN_COLORS["ink"]),
            cliponaxis=False,
        )
        subfield_count_max = max(float(subfield_count_plot["active_companies"].max()), 1.0)
        figures["physical_ai_subfield_counts"].update_layout(
            height=470,
            margin=dict(l=214, r=42, t=72, b=46),
            showlegend=False,
            yaxis=dict(title=None, automargin=True),
            xaxis=dict(title=None, range=[0, subfield_count_max * 1.16]),
        )

        funding_plot = subfield_df.sort_values("funding_base_usd_b", ascending=True)
        figures["physical_ai_subfield_funding"] = px.bar(
            funding_plot,
            x="funding_base_usd_b",
            y="company_subfield",
            orientation="h",
            text="funding_label",
            template=template,
            error_x=funding_plot["funding_high_usd_b"] - funding_plot["funding_base_usd_b"],
            error_x_minus=funding_plot["funding_base_usd_b"] - funding_plot["funding_low_usd_b"],
            labels={"funding_base_usd_b": "Estimated investment, base (USD B)", "company_subfield": ""},
            title="Estimated Physical AI funding by sub-field",
            hover_data={
                "active_companies": True,
                "top_regions": True,
                "metric_caution_rows": True,
                "funding_label": False,
            },
        )
        figures["physical_ai_subfield_funding"].update_traces(
            marker_color=DESIGN_COLORS["value_capture"],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color=DESIGN_COLORS["ink"]),
            cliponaxis=False,
        )
        figures["physical_ai_subfield_funding"].update_layout(
            height=520,
            margin=dict(l=214, r=28, t=72, b=58),
            showlegend=False,
            yaxis=dict(title=None, automargin=True),
            xaxis=dict(title="Estimated investment, base (USD B)", rangemode="tozero"),
        )

    if physical_ai_company_region_summary is not None and not physical_ai_company_region_summary.empty:
        region_df = physical_ai_company_region_summary.copy()
        region_df["funding_base_usd_b"] = region_df["investment_base_usd_m"] / 1000.0
        region_df["funding_low_usd_b"] = region_df["investment_low_usd_m"] / 1000.0
        region_df["funding_high_usd_b"] = region_df["investment_high_usd_m"] / 1000.0
        region_df["bubble_size"] = region_df["funding_base_usd_b"].clip(lower=0.18)
        region_colors = {
            "US": DESIGN_COLORS["origin"],
            "EU / Europe": DESIGN_COLORS["mixed_origin"],
            "China / Asia": DESIGN_COLORS["china"],
            "Canada": "#0891b2",
            "Latin America": DESIGN_COLORS["success"],
            "Other / mixed": DESIGN_COLORS["warning"],
        }
        figures["physical_ai_region_bubble"] = px.scatter(
            region_df,
            x="active_companies",
            y="funding_base_usd_b",
            size="bubble_size",
            color="strategic_region",
            text="strategic_region",
            template=template,
            color_discrete_map=region_colors,
            size_max=58,
            labels={
                "active_companies": "Active companies",
                "funding_base_usd_b": "Estimated investment, base (USD B)",
                "strategic_region": "Strategic region",
            },
            title="Strategic regions: company count vs estimated funding",
            hover_data={
                "investment_low_usd_m": ":,.0f",
                "investment_base_usd_m": ":,.0f",
                "investment_high_usd_m": ":,.0f",
                "top_subfields": True,
                "metric_caution_rows": True,
                "bubble_size": False,
            },
        )
        max_count = max(float(region_df["active_companies"].max()), 1.0)
        max_funding = max(float(region_df["funding_base_usd_b"].max()), 1.0)
        figures["physical_ai_region_bubble"].update_traces(
            textposition="top center",
            marker=dict(line=dict(color="#ffffff", width=1.5), opacity=0.86),
            cliponaxis=False,
        )
        figures["physical_ai_region_bubble"].update_layout(
            height=520,
            margin=dict(l=70, r=40, t=80, b=68),
            legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0, title_text=""),
            xaxis=dict(range=[-0.5, max_count + 2], dtick=2),
            yaxis=dict(range=[-0.4, max_funding * 1.30], zeroline=True),
        )

    inst_counts = cleaned["institution_clean"].value_counts().reset_index().head(20)
    inst_counts.columns = ["institution", "papers"]
    figures["institution_leaderboard"] = px.bar(
        inst_counts,
        x="papers",
        y="institution",
        orientation="h",
        template=template,
        labels={"papers": "Papers", "institution": "Institution"},
        title="Institution leaderboard",
    )
    figures["institution_leaderboard"].update_traces(marker_color=DESIGN_COLORS["origin"])
    figures["institution_leaderboard"].update_layout(yaxis={"categoryorder": "total ascending"})

    heat = (
        origin_long[origin_long["origin_country"].ne("")]
        .pivot_table(index="origin_country", columns="broad_area_clean", values="paper_id", aggfunc="nunique", fill_value=0)
        .astype(int)
    )
    heat = heat.loc[heat.sum(axis=1).sort_values(ascending=False).head(15).index]
    figures["country_area_heatmap"] = px.imshow(
        heat,
        template=template,
        labels={"x": "Broad area", "y": "Origin country", "color": "Papers"},
        title="Origin country x broad-area heatmap",
        aspect="auto",
    )

    if flow_df is not None and not flow_df.empty:
        flow_plot = flow_df.copy()
        flow_plot["country_capture_share_pct"] = pd.to_numeric(flow_plot["country_capture_share"], errors="coerce") * 100
        map_df = (
            flow_plot.groupby(["beneficiary_country", "beneficiary_country_iso3", "scenario"], dropna=False)
            .agg(
                papers=("paper_id", "nunique"),
                total_capture_share_pct=("country_capture_share_pct", "sum"),
                average_capture_share_pct=("country_capture_share_pct", "mean"),
            )
            .reset_index()
        )
        figures["beneficiary_value_map_v02"] = px.choropleth(
            map_df,
            locations="beneficiary_country_iso3",
            color="total_capture_share_pct",
            hover_name="beneficiary_country",
            animation_frame="scenario",
            color_continuous_scale="Cividis",
            template=template,
            labels={
                "total_capture_share_pct": "Sum of partial capture-share assumptions (%)",
                "scenario": "Scenario",
            },
            title="Beneficiary-country value map (partial capture-share layer)",
        )
        figures["beneficiary_value_map_v02"].update_geos(showframe=False, showcoastlines=True)

        base_flow = flow_plot[flow_plot["scenario"].eq("base")].copy()
        if not base_flow.empty:
            beneficiary_counts = (
                base_flow.groupby("beneficiary_country")["paper_id"].nunique().rename("beneficiary_papers").reset_index()
            )
            origin_compare = origin_counts.rename(columns={"origin_country": "country", "papers": "origin_papers"})[
                ["country", "origin_papers"]
            ]
            beneficiary_compare = beneficiary_counts.rename(columns={"beneficiary_country": "country"})
            compare = origin_compare.merge(beneficiary_compare, on="country", how="outer").fillna(0)
            compare = compare.sort_values(["beneficiary_papers", "origin_papers"], ascending=False).head(20)
            compare_long = compare.melt(
                id_vars="country",
                value_vars=["origin_papers", "beneficiary_papers"],
                var_name="metric",
                value_name="papers",
            )
            figures["origin_vs_beneficiary_bar"] = px.bar(
                compare_long,
                x="papers",
                y="country",
                color="metric",
                barmode="group",
                orientation="h",
                template=template,
                labels={"papers": "Papers", "country": "Country", "metric": "Metric"},
                title="Origin count vs beneficiary count (partial benefit layer)",
            )
            figures["origin_vs_beneficiary_bar"].update_layout(yaxis={"categoryorder": "total ascending"})

            heat_rows = []
            for _, row in base_flow.iterrows():
                origins = [part.strip() for part in clean_text(row["origin_country"]).split(";") if part.strip()]
                for origin in origins or ["Unknown"]:
                    heat_rows.append(
                        {
                            "origin_country": origin,
                            "beneficiary_country": row["beneficiary_country"],
                            "capture_share_pct": row["country_capture_share_pct"],
                        }
                    )
            heat_df = pd.DataFrame(heat_rows)
            if not heat_df.empty:
                heat_matrix = heat_df.pivot_table(
                    index="origin_country",
                    columns="beneficiary_country",
                    values="capture_share_pct",
                    aggfunc="sum",
                    fill_value=0,
                )
                figures["origin_beneficiary_heatmap"] = px.imshow(
                    heat_matrix,
                    template=template,
                    labels={
                        "x": "Beneficiary country",
                        "y": "Origin country",
                        "color": "Base capture-share sum (%)",
                    },
                    title="Origin country x beneficiary country heatmap (base, partial layer)",
                    aspect="auto",
                )

            sankey_base = base_flow.rename(
                columns={
                    "origin_country": "origin_country",
                    "field_or_platform": "field_or_platform",
                    "beneficiary_country": "beneficiary_country",
                }
            )
            figures["origin_to_beneficiary_sankey_v02"] = make_sankey(
                sankey_base.head(120),
                ["origin_country", "field_or_platform", "beneficiary_country"],
                "Origin country -> field/platform -> beneficiary country (base, partial layer)",
            )

    if public_private_spillover is not None and not public_private_spillover.empty:
        pp_base = public_private_spillover[public_private_spillover["scenario"].eq("base")].copy()
        if not pp_base.empty:
            figures["public_private_spillover"] = px.bar(
                pp_base,
                x="papers",
                y="public_private_origin",
                color="beneficiary_role",
                orientation="h",
                template=template,
                labels={
                    "papers": "Beneficiary papers",
                    "public_private_origin": "Research-origin type",
                    "beneficiary_role": "Beneficiary role",
                },
                title="Public/private research origin -> China beneficiary roles (base, partial layer)",
            )
            figures["public_private_spillover"].update_layout(yaxis={"categoryorder": "total ascending"})

    if not country_summary.empty and country_summary["revenue_capture_base_usd"].fillna(0).sum() > 0:
        value_df = country_summary.sort_values("revenue_capture_base_usd", ascending=False).head(20)
        figures["value_capture_bar"] = px.bar(
            value_df,
            x="revenue_capture_base_usd",
            y="beneficiary_country",
            orientation="h",
            template=template,
            error_x=value_df["revenue_capture_high_usd"] - value_df["revenue_capture_base_usd"],
            error_x_minus=value_df["revenue_capture_base_usd"] - value_df["revenue_capture_low_usd"],
            labels={"revenue_capture_base_usd": "Estimated value captured, base", "beneficiary_country": "Country"},
            title="Beneficiary countries by estimated value captured",
        )
        figures["value_capture_bar"].update_layout(yaxis={"categoryorder": "total ascending"})

        profit_df = country_summary.sort_values("profit_proxy_base_usd", ascending=False).head(20)
        figures["profit_proxy_bar"] = px.bar(
            profit_df,
            x="profit_proxy_base_usd",
            y="beneficiary_country",
            orientation="h",
            template=template,
            labels={"profit_proxy_base_usd": "Estimated operating-profit proxy, base", "beneficiary_country": "Country"},
            title="Beneficiary countries by estimated profit proxy",
        )
        figures["profit_proxy_bar"].update_layout(yaxis={"categoryorder": "total ascending"})

        map_df = country_summary[country_summary["beneficiary_country_iso3"].ne("")]
        figures["value_capture_map"] = px.choropleth(
            map_df,
            locations="beneficiary_country_iso3",
            color="revenue_capture_base_usd",
            hover_name="beneficiary_country",
            color_continuous_scale="Cividis",
            template=template,
            labels={"revenue_capture_base_usd": "Estimated value captured"},
            title="Estimated beneficiary-country value capture map",
        )
        figures["value_capture_map"].update_geos(showframe=False, showcoastlines=True)

    if not benefit_estimates.empty:
        flow_df = benefit_estimates.copy()
        flow_df["paper_short"] = flow_df["paper_or_discovery"].map(lambda x: clean_text(x)[:55])
        flow_df["origin_country"] = flow_df["origin_country_list"].map(lambda x: clean_text(x).split("; ")[0] if clean_text(x) else "")
        flow_df = flow_df[
            flow_df["origin_country"].ne("")
            & flow_df["beneficiary_country"].map(clean_text).ne("")
            & flow_df["paper_short"].ne("")
        ].head(60)
        if not flow_df.empty:
            figures["origin_to_beneficiary_sankey"] = make_sankey(
                flow_df,
                ["origin_country", "paper_short", "beneficiary_country"],
                "Research origin -> paper/platform -> beneficiary country (structure only)",
            )

        role_df = benefit_estimates[benefit_estimates["beneficiary_role"].map(clean_text).ne("")]
        if not role_df.empty:
            figures["role_to_country_sankey"] = make_sankey(
                role_df.head(80),
                ["beneficiary_role", "beneficiary_country"],
                "Beneficiary role -> country (structure only)",
            )

        for region_key, region_label, iso3_set in [
            ("us", "US", {"USA"}),
            ("eu", "EU", EU_MEMBER_ISO3),
        ]:
            region_df = benefit_estimates[
                benefit_estimates["beneficiary_country_iso3"].map(clean_text).isin(iso3_set)
            ].copy()
            if region_df.empty:
                continue
            region_df["origin_country"] = region_df["origin_country_list"].map(clean_text)
            region_df["platform_label"] = region_df["field_or_platform"].map(lambda value: short_label(value, 58))
            region_df["region_role"] = region_df["beneficiary_role"].map(
                lambda value: f"{region_label} role: {format_role_label(value)}"
            )
            figures[f"{region_key}_origin_platform_role_sankey"] = make_sankey(
                region_df,
                ["origin_country", "platform_label", "region_role"],
                f"Origin -> platform -> {region_label} value-capture role",
            )

    if china_update is not None and not china_update.empty:
        china_plot = china_update.copy()
        broad_lookup = cleaned.set_index("paper_id")["broad_area_clean"].to_dict()
        china_plot["broad_area_clean"] = china_plot["paper_id"].map(broad_lookup).fillna("Unclassified")
        china_plot = china_plot.sort_values("Revenue_capture_share_base_pct", ascending=False)

        role_counts = (
            china_plot.groupby("beneficiary_role_canonical")["paper_id"]
            .nunique()
            .reset_index(name="papers")
            .sort_values("papers", ascending=False)
        )
        figures["china_role_mix"] = px.bar(
            role_counts,
            x="papers",
            y="beneficiary_role_canonical",
            orientation="h",
            template=template,
            labels={"papers": "China beneficiary papers", "beneficiary_role_canonical": "Primary value-capture role"},
            title="China beneficiary role mix",
        )
        figures["china_role_mix"].update_traces(marker_color=DESIGN_COLORS["china"])
        figures["china_role_mix"].update_layout(yaxis={"categoryorder": "total ascending"})

        confidence_counts = (
            china_plot.groupby(["Benefit_strength", "Benefit_confidence"])["paper_id"]
            .nunique()
            .reset_index(name="papers")
        )
        figures["china_strength_confidence"] = px.bar(
            confidence_counts,
            x="Benefit_strength",
            y="papers",
            color="Benefit_confidence",
            barmode="group",
            template=template,
            labels={"papers": "Papers", "Benefit_strength": "Benefit strength", "Benefit_confidence": "Confidence"},
            title="China benefit strength and confidence",
        )

        sankey_df = pd.DataFrame(
            {
                "origin_country": china_plot["Origin_country_or_countries"],
                "field_or_platform": china_plot["Field_or_platform"],
                "china_role": china_plot["beneficiary_role_canonical"].map(lambda value: f"China role: {value}"),
            }
        )
        figures["china_origin_platform_role_sankey"] = make_sankey(
            sankey_df,
            ["origin_country", "field_or_platform", "china_role"],
            "Origin -> platform -> China value-capture role",
        )

    custom_layout_figures = {
        "physical_intelligence_capabilities",
        "physical_intelligence_domains",
        "physical_intelligence_sankey",
        "physical_ai_country_counts",
        "physical_ai_subfield_counts",
        "physical_ai_subfield_funding",
        "physical_ai_region_bubble",
    }
    for name, fig in figures.items():
        fig.update_layout(
            font=dict(family="Inter, Arial, sans-serif", size=12),
            title_font=dict(size=18),
        )
        if name not in custom_layout_figures:
            fig.update_layout(margin=dict(l=20, r=20, t=64, b=35))
    return figures


def make_sankey(df: pd.DataFrame, cols: list[str], title: str) -> go.Figure:
    labels: list[str] = []
    label_index: dict[str, int] = {}
    sources: list[int] = []
    targets: list[int] = []
    values: list[float] = []

    def get_label_id(label: str) -> int:
        if label not in label_index:
            label_index[label] = len(labels)
            labels.append(label)
        return label_index[label]

    for left, right in zip(cols[:-1], cols[1:]):
        edges = (
            df[[left, right]]
            .fillna("")
            .map(clean_text)
            .query(f"`{left}` != '' and `{right}` != ''")
            .groupby([left, right])
            .size()
            .reset_index(name="weight")
        )
        for _, edge in edges.iterrows():
            sources.append(get_label_id(edge[left]))
            targets.append(get_label_id(edge[right]))
            values.append(float(edge["weight"]))

    return go.Figure(
        data=[
            go.Sankey(
                node=dict(label=labels, pad=15, thickness=14),
                link=dict(source=sources, target=targets, value=values),
            )
        ],
        layout=go.Layout(title=title, template="plotly_white"),
    )


def dataframe_to_html_table(df: pd.DataFrame, table_id: str, columns: list[str] | None = None, max_rows: int | None = None) -> str:
    view = df.copy()
    if columns:
        view = view[columns]
    if max_rows is not None:
        view = view.head(max_rows)
    return view.to_html(
        index=False,
        table_id=table_id,
        classes="data-table",
        border=0,
        escape=True,
        na_rep="",
    )


def build_assumption_coverage_table(assumptions: pd.DataFrame, max_rows: int = 20) -> str:
    if assumptions.empty:
        return '<p class="muted">No country-benefit assumption rows have been generated yet.</p>'
    coverage = (
        assumptions.groupby(["paper_id", "paper_or_discovery"], dropna=False)
        .agg(
            assumption_rows=("paper_id", "size"),
            beneficiary_countries=("beneficiary_country", lambda s: len({clean_text(v) for v in s if clean_text(v)})),
            beneficiary_roles=("beneficiary_role", lambda s: "; ".join(sorted({clean_text(v) for v in s if clean_text(v)}))),
        )
        .reset_index()
        .sort_values(["assumption_rows", "beneficiary_countries"], ascending=False)
        .head(max_rows)
    )
    return dataframe_to_html_table(
        coverage,
        "assumption-coverage",
        ["paper_id", "paper_or_discovery", "assumption_rows", "beneficiary_countries", "beneficiary_roles"],
    )


def build_filter_options(values: pd.Series) -> str:
    opts = ['<option value="">All</option>']
    for value in sorted([clean_text(v) for v in values.dropna().unique() if clean_text(v)]):
        opts.append(f'<option value="{html.escape(value)}">{html.escape(value)}</option>')
    return "\n".join(opts)


def fig_to_html_fragments(figures: dict[str, go.Figure]) -> dict[str, str]:
    fragments = {}
    include_plotlyjs = True
    for name, fig in figures.items():
        fragments[name] = pio.to_html(fig, full_html=False, include_plotlyjs=include_plotlyjs, config=MODEBAR_CONFIG)
        include_plotlyjs = False
    return fragments


def write_dashboard_html(
    cleaned: pd.DataFrame,
    origin_long: pd.DataFrame,
    assumptions: pd.DataFrame,
    benefit_estimates: pd.DataFrame,
    country_summary: pd.DataFrame,
    china_update: pd.DataFrame,
    china_summary: pd.DataFrame,
    origin_country_summary: pd.DataFrame,
    origin_to_beneficiary_flow: pd.DataFrame,
    field_country_summary: pd.DataFrame,
    public_private_spillover_summary: pd.DataFrame,
    quality_check_report: pd.DataFrame,
    physical_intelligence_links: pd.DataFrame,
    physical_intelligence_domain_summary: pd.DataFrame,
    physical_ai_companies_clean: pd.DataFrame,
    physical_ai_country_summary: pd.DataFrame,
    physical_ai_subfield_summary: pd.DataFrame,
    physical_ai_region_summary: pd.DataFrame,
    quality_checks: dict[str, pd.DataFrame | int],
    assumption_warnings: pd.DataFrame,
    instructions_md: str,
    input_csv_path: str = INPUT_CSV,
    output_path: str | Path = OUTPUT_HTML,
) -> None:
    figures = make_figures(
        cleaned,
        origin_long,
        benefit_estimates,
        country_summary,
        china_update,
        origin_to_beneficiary_flow,
        public_private_spillover_summary,
        physical_intelligence_links,
        physical_intelligence_domain_summary,
        physical_ai_country_summary,
        physical_ai_subfield_summary,
        physical_ai_region_summary,
    )
    fig_html = fig_to_html_fragments(figures)
    plotly_loader = pio.to_html(go.Figure(), full_html=False, include_plotlyjs=True, config=MODEBAR_CONFIG)

    total_papers = len(cleaned)
    year_values = cleaned["year_int"].dropna().astype(int)
    year_range = f"{year_values.min()}-{year_values.max()}" if not year_values.empty else "n/a"
    origin_country_count = origin_long[origin_long["origin_country_iso3"].ne("")]["origin_country"].nunique()
    beneficiary_country_count = assumptions[assumptions["beneficiary_country_iso3"].ne("")]["beneficiary_country"].nunique()
    top_origin = (
        origin_long[origin_long["origin_country"].ne("")]
        .groupby("origin_country")["paper_id"]
        .nunique()
        .sort_values(ascending=False)
    )
    top_origin_text = top_origin.index[0] if not top_origin.empty else "n/a"
    total_value_base = (
        country_summary["revenue_capture_base_usd"].sum(min_count=1)
        if not country_summary.empty and "revenue_capture_base_usd" in country_summary.columns
        else np.nan
    )
    has_value_estimates = pd.notna(total_value_base) and total_value_base > 0
    if has_value_estimates:
        value_status = f"{format_usd(total_value_base)} base"
    elif not china_update.empty:
        value_status = "China share view loaded"
    else:
        value_status = "Ready for assumptions"

    kpis = [
        ("Total papers", f"{total_papers:,}"),
        ("Year range", year_range),
        ("Research-origin countries", f"{origin_country_count:,}"),
        ("Top research-origin country", top_origin_text),
        ("Value model status", value_status),
        ("Beneficiary countries drafted", f"{beneficiary_country_count:,}"),
    ]
    kpi_html = "\n".join(
        f'<div class="metric"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>' for label, value in kpis
    )

    if not china_update.empty:
        china_base_share = pd.to_numeric(china_update["Revenue_capture_share_base_pct"], errors="coerce")
        china_high_conf = china_update["Benefit_confidence"].map(clean_text).isin(["High", "Medium-high"]).sum()
        china_very_high = china_update["Benefit_strength"].map(clean_text).eq("Very high").sum()
        china_top = china_update.loc[china_base_share.idxmax()] if china_base_share.notna().any() else None
        china_kpis = [
            ("China beneficiary papers", f"{china_update['paper_id'].nunique():,}"),
            ("Average base capture share", f"{china_base_share.mean():.1f}%"),
            ("Median base capture share", f"{china_base_share.median():.1f}%"),
            ("High confidence rows", f"{int(china_high_conf):,}"),
            ("Very high strength rows", f"{int(china_very_high):,}"),
            (
                "Highest base share",
                f"{clean_text(china_top['Field_or_platform'])[:32]}: {float(china_top['Revenue_capture_share_base_pct']):.0f}%"
                if china_top is not None
                else "n/a",
            ),
        ]
        china_kpi_html = "\n".join(
            f'<div class="metric small"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
            for label, value in china_kpis
        )
    else:
        china_kpi_html = '<p class="muted">No China value-capture update file found.</p>'

    explorer_cols = [
        "ID",
        "Confidence_tier",
        "Year",
        "Broad_area",
        "Field_or_platform",
        "Paper_or_discovery",
        "Country_or_countries",
        "Institution_at_publication",
        "DOI_or_link",
    ]
    table_df = cleaned[explorer_cols + ["confidence_tier_clean", "broad_area_clean", "origin_country_list", "public_private_clean"]].copy()
    data_rows = []
    for _, row in table_df.iterrows():
        attr = {
            "confidence": row["confidence_tier_clean"],
            "area": row["broad_area_clean"],
            "origin": row["origin_country_list"],
            "publicprivate": row["public_private_clean"],
        }
        attrs = " ".join(f'data-{k}="{html.escape(str(v))}"' for k, v in attr.items())
        cells = "".join(f"<td>{html.escape(clean_text(row[col]))}</td>" for col in explorer_cols)
        data_rows.append(f"<tr {attrs}>{cells}</tr>")
    explorer_table = f"""
    <table id="papers-table" class="data-table">
      <thead><tr>{''.join(f'<th>{html.escape(col)}</th>' for col in explorer_cols)}</tr></thead>
      <tbody>{''.join(data_rows)}</tbody>
    </table>
    """
    company_cols = [
        ("company_name", "Company"),
        ("country_list", "Country"),
        ("strategic_region", "Strategic region"),
        ("company_subfield", "Sub-field"),
        ("physical_ai_use", "Physical AI use"),
        ("active_status", "Active status"),
        ("investment_range", "Investment range"),
        ("investment_confidence", "Evidence confidence"),
        ("latest_round_or_event", "Latest round/event"),
        ("source_links", "Sources"),
    ]
    company_rows = []
    company_table_df = physical_ai_companies_clean.copy()
    if not company_table_df.empty:
        for _, row in company_table_df.iterrows():
            low = pd.to_numeric(row.get("investment_low_usd_m"), errors="coerce")
            base = pd.to_numeric(row.get("investment_base_usd_m"), errors="coerce")
            high = pd.to_numeric(row.get("investment_high_usd_m"), errors="coerce")
            if pd.notna(base):
                if pd.notna(low) and pd.notna(high) and (not math.isclose(low, base) or not math.isclose(high, base)):
                    investment_range = f"{format_usd(low * 1_000_000)} / {format_usd(base * 1_000_000)} / {format_usd(high * 1_000_000)}"
                else:
                    investment_range = format_usd(base * 1_000_000)
            else:
                investment_range = "Not estimated"
            row_view = row.to_dict()
            row_view["investment_range"] = investment_range
            row_view["source_links"] = linkify(clean_text(row.get("source_urls")))
            caution = bool(clean_text(row.get("do_not_aggregate_without_metric_filter")))
            attr = {
                "region": clean_text(row.get("strategic_region")),
                "country": clean_text(row.get("country_list")),
                "subfield": clean_text(row.get("company_subfield")),
                "status": clean_text(row.get("active_status")),
                "confidence": clean_text(row.get("investment_confidence")),
                "caution": "yes" if caution else "no",
            }
            attrs = " ".join(f'data-{k}="{html.escape(str(v))}"' for k, v in attr.items())
            cells = []
            for col, _label in company_cols:
                value = row_view.get(col, "")
                if col == "source_links":
                    cells.append(f"<td>{value}</td>")
                else:
                    cells.append(f"<td>{html.escape(clean_text(value))}</td>")
            company_rows.append(f"<tr {attrs}>{''.join(cells)}</tr>")
    company_explorer_table = f"""
    <table id="companies-table" class="data-table">
      <thead><tr>{''.join(f'<th>{html.escape(label)}</th>' for _, label in company_cols)}</tr></thead>
      <tbody>{''.join(company_rows)}</tbody>
    </table>
    """
    company_filter_series = (
        physical_ai_companies_clean if not physical_ai_companies_clean.empty else pd.DataFrame()
    )
    company_filter_options = {
        "region": build_filter_options(company_filter_series.get("strategic_region", pd.Series(dtype=str))),
        "country": build_filter_options(company_filter_series.get("country_list", pd.Series(dtype=str))),
        "subfield": build_filter_options(company_filter_series.get("company_subfield", pd.Series(dtype=str))),
        "status": build_filter_options(company_filter_series.get("active_status", pd.Series(dtype=str))),
        "confidence": build_filter_options(company_filter_series.get("investment_confidence", pd.Series(dtype=str))),
    }

    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M %Z").strip()

    china_origin_count = int(cleaned["has_china_origin"].sum()) if "has_china_origin" in cleaned.columns else 0
    china_beneficiary_count = int(china_update["paper_id"].nunique()) if not china_update.empty else 0
    beneficiary_iso3 = (
        assumptions["beneficiary_country_iso3"].map(clean_text)
        if "beneficiary_country_iso3" in assumptions.columns
        else pd.Series(dtype=str)
    )
    us_beneficiary_count = int(assumptions[beneficiary_iso3.eq("USA")]["paper_id"].nunique()) if not assumptions.empty else 0
    eu_beneficiary_count = int(assumptions[beneficiary_iso3.isin(EU_MEMBER_ISO3)]["paper_id"].nunique()) if not assumptions.empty else 0
    eu_country_count = (
        int(assumptions[beneficiary_iso3.isin(EU_MEMBER_ISO3)]["beneficiary_country"].map(clean_text).nunique())
        if not assumptions.empty
        else 0
    )
    china_share_mean = (
        pd.to_numeric(china_update["Revenue_capture_share_base_pct"], errors="coerce").mean()
        if not china_update.empty
        else np.nan
    )
    platform_presence = core_platform_presence(cleaned)
    present_platform_count = int(platform_presence["status"].eq("present").sum())
    platform_count = len(platform_presence)
    present_platforms = ", ".join(
        platform_presence[platform_presence["status"].eq("present")]["platform"].head(8).tolist()
    )
    direct_pi_papers = (
        int(
            physical_intelligence_links[
                physical_intelligence_links["pi_relevance"].eq("Direct physical-intelligence substrate")
            ]["paper_id"].nunique()
        )
        if not physical_intelligence_links.empty
        else 0
    )
    ai_model_papers = (
        int(
            physical_intelligence_links[
                physical_intelligence_links["pi_platform_family"].eq("AI models and prediction")
            ]["paper_id"].nunique()
        )
        if not physical_intelligence_links.empty
        else 0
    )
    pi_capability_count = (
        int(physical_intelligence_links["pi_capability"].nunique()) if not physical_intelligence_links.empty else 0
    )
    science_domain_count = (
        int(physical_intelligence_domain_summary["science_acceleration_domain"].nunique())
        if not physical_intelligence_domain_summary.empty
        else 0
    )
    top_science_domains = (
        ", ".join(physical_intelligence_domain_summary["science_acceleration_domain"].head(4).tolist())
        if not physical_intelligence_domain_summary.empty
        else "No domains classified yet"
    )
    story_cards = [
        (
            "1",
            "First wave: platform papers",
            f"{present_platform_count}/{platform_count} target platform families present.",
            f"The list covers foundations such as {present_platforms}. These are enabling platforms, not direct company revenue claims.",
            "origin",
        ),
        (
            "2",
            "Generative-AI bridge",
            f"{ai_model_papers} AI-model / prediction papers linked.",
            "The generative-AI wave converted knowledge into language, images, code, predictions, and reusable model interfaces.",
            "origin",
        ),
        (
            "3",
            "Physical Intelligence thesis",
            f"{direct_pi_papers} papers map to direct physical-world substrates.",
            "The thesis is that AI systems increasingly perceive, simulate, plan, manipulate, manufacture, synthesize, test, measure, and learn from the physical world.",
            "value",
        ),
        (
            "4",
            "Science acceleration",
            f"{science_domain_count} acceleration domains classified.",
            f"The current thesis layer links papers to domains including {top_science_domains}. This layer is rule-based and should be audited.",
            "value",
        ),
        (
            "5",
            "Value capture and strategy",
            f"US rows: {us_beneficiary_count}; EU rows: {eu_beneficiary_count}; China rows: {china_beneficiary_count}.",
            "Strategic advantage depends on origin, IP, cloud, manufacturing, adoption, and evidence quality. The country layer remains modeled and incomplete.",
            "china",
        ),
        (
            "6",
            "Stress test",
            "Likely is not guaranteed.",
            "The thesis weakens if robotics deployment, lab automation, physical-data quality, capex, regulation, or audited revenue evidence do not scale.",
            "warning",
        ),
    ]
    story_cards_html = "\n".join(
        f"""
        <article class="story-card {html.escape(kind)}">
          <span class="step" aria-hidden="true">{html.escape(step)}</span>
          <h3>{html.escape(title)}</h3>
          <p class="story-stat">{html.escape(stat)}</p>
          <p>{html.escape(body)}</p>
        </article>
        """
        for step, title, stat, body, kind in story_cards
    )
    thesis_company_cards = [
        (
            "Robot foundation-model companies",
            "Models that connect perception, planning, and control to manipulation or mobility.",
        ),
        (
            "Automated lab and foundry operators",
            "Closed-loop systems that design, synthesize, test, measure, and update models from experimental feedback.",
        ),
        (
            "AI materials and bio-design platforms",
            "Prediction and generation systems connected to chemistry, protein, cell, materials, and manufacturing workflows.",
        ),
        (
            "Industrial autonomy providers",
            "Systems that combine sensors, simulation, cloud/data infrastructure, and process control in factories and supply chains.",
        ),
    ]
    thesis_company_cards_html = "\n".join(
        f"""
        <article class="thesis-card">
          <h3>{html.escape(title)}</h3>
          <p>{html.escape(body)}</p>
        </article>
        """
        for title, body in thesis_company_cards
    )
    if not physical_ai_companies_clean.empty:
        company_count = int(physical_ai_companies_clean["company_name"].nunique())
        company_country_count = int(physical_ai_country_summary["country"].nunique()) if not physical_ai_country_summary.empty else 0
        company_subfield_count = (
            int(physical_ai_subfield_summary["company_subfield"].nunique())
            if not physical_ai_subfield_summary.empty
            else 0
        )
        company_base_funding_m = pd.to_numeric(
            physical_ai_companies_clean["investment_base_usd_m"], errors="coerce"
        ).sum(min_count=1)
        top_company_country = (
            clean_text(physical_ai_country_summary.iloc[0]["country"])
            if not physical_ai_country_summary.empty
            else "n/a"
        )
        top_region_by_funding = (
            clean_text(
                physical_ai_region_summary.sort_values("investment_base_usd_m", ascending=False).iloc[0][
                    "strategic_region"
                ]
            )
            if not physical_ai_region_summary.empty
            else "n/a"
        )
        company_landscape_kpis = [
            ("Active companies", f"{company_count:,}"),
            ("Countries represented", f"{company_country_count:,}"),
            ("Physical AI sub-fields", f"{company_subfield_count:,}"),
            ("Base investment estimate", f"${company_base_funding_m / 1000.0:.1f}B" if pd.notna(company_base_funding_m) else "n/a"),
            ("Top country by count", top_company_country),
            ("Top region by funding", top_region_by_funding),
        ]
        company_landscape_kpi_html = "\n".join(
            f'<div class="metric small"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
            for label, value in company_landscape_kpis
        )
    else:
        company_landscape_kpi_html = (
            f'<p class="muted">No active company dataset found. Add {html.escape(PHYSICAL_AI_COMPANIES_CSV)} '
            "to render the company landscape charts.</p>"
        )

    def build_region_revenue_card(
        label: str,
        iso3_set: set[str],
        layer_note: str,
        paper_count_override: int | None = None,
        country_count_override: int | None = None,
    ) -> str:
        region_assumptions = (
            assumptions[beneficiary_iso3.isin(iso3_set)].copy()
            if not assumptions.empty and "beneficiary_country_iso3" in assumptions.columns
            else pd.DataFrame()
        )
        region_summary = (
            country_summary[country_summary["beneficiary_country_iso3"].map(clean_text).isin(iso3_set)].copy()
            if not country_summary.empty and "beneficiary_country_iso3" in country_summary.columns
            else pd.DataFrame()
        )

        def sum_revenue(col: str) -> float:
            if region_summary.empty or col not in region_summary.columns:
                return np.nan
            return pd.to_numeric(region_summary[col], errors="coerce").sum(min_count=1)

        low = sum_revenue("revenue_capture_low_usd")
        base = sum_revenue("revenue_capture_base_usd")
        high = sum_revenue("revenue_capture_high_usd")
        has_revenue = pd.notna(base)
        total_text = format_usd(base) if has_revenue else "Not estimated yet"
        range_text = (
            f"Low-high range: {format_usd(low)} to {format_usd(high)}"
            if has_revenue
            else "Missing enabled-revenue and attribution denominators."
        )
        paper_count = (
            paper_count_override
            if paper_count_override is not None
            else int(region_assumptions["paper_id"].nunique()) if not region_assumptions.empty else 0
        )
        country_count = (
            country_count_override
            if country_count_override is not None
            else int(region_assumptions["beneficiary_country"].map(clean_text).nunique())
            if not region_assumptions.empty and "beneficiary_country" in region_assumptions.columns
            else 0
        )
        roles = (
            ", ".join(
                sorted({format_role_label(value) for value in region_assumptions["beneficiary_role"] if clean_text(value)})[:4]
            )
            if not region_assumptions.empty and "beneficiary_role" in region_assumptions.columns
            else "No role rows"
        )
        status = "Revenue total available" if has_revenue else "Coverage only"
        status_class = "estimated" if has_revenue else "missing"
        return f"""
          <article class="revenue-card {status_class}">
            <span>{html.escape(label)}</span>
            <strong>{html.escape(total_text)}</strong>
            <p>{html.escape(range_text)}</p>
            <dl>
              <div><dt>Status</dt><dd>{html.escape(status)}</dd></div>
              <div><dt>Beneficiary papers</dt><dd>{paper_count:,}</dd></div>
              <div><dt>Countries</dt><dd>{country_count:,}</dd></div>
              <div><dt>Roles</dt><dd>{html.escape(roles)}</dd></div>
            </dl>
            <p class="revenue-note">{html.escape(layer_note)}</p>
          </article>
        """

    region_revenue_panel_html = f"""
      <section class="revenue-capture" aria-labelledby="revenue-capture-title">
        <div class="compare-head">
          <h3 id="revenue-capture-title">Total Revenue Captured: US, EU, and China</h3>
          <p><strong>Fair accounting rule:</strong> revenue capture needs enabled market revenue, paper attribution, and country capture share. The current files contain role/share coverage, but no populated dollar denominators, so the dashboard does not invent dollar totals.</p>
        </div>
        <div class="revenue-grid" role="list" aria-label="US EU China total revenue-capture status">
          {build_region_revenue_card("China", {"CHN"}, "China has a partial capture-share layer; dollar revenue totals require platform-level enabled revenue.", china_beneficiary_count, 1 if china_beneficiary_count else 0)}
          {build_region_revenue_card("United States", {"USA"}, "US rows are modeled assumptions, currently strongest for headquarters and research-origin roles.")}
          {build_region_revenue_card("European Union", EU_MEMBER_ISO3, "EU rows aggregate current EU member-state assumptions; current coverage is partial.")}
        </div>
      </section>
    """

    benefit_multiplier = china_beneficiary_count / max(china_origin_count, 1)
    china_comparison_html = f"""
      <section class="china-compare" aria-labelledby="china-compare-title">
        <div class="compare-head">
          <h3 id="china-compare-title">Origin-only counting misses the scaling story</h3>
          <p>China appears as a research-origin country for <strong>{china_origin_count}</strong> paper, but as a beneficiary/value-capture country for <strong>{china_beneficiary_count}</strong> papers in the current partial layer.</p>
        </div>
        <div class="compare-row" role="list" aria-label="China origin versus beneficiary count">
          <div class="compare-metric origin" role="listitem">
            <span>Research-origin view</span>
            <strong>{china_origin_count}</strong>
            <em>paper entry</em>
          </div>
          <div class="compare-arrow" aria-hidden="true">&rarr;</div>
          <div class="compare-metric china" role="listitem">
            <span>Beneficiary/value-capture view</span>
            <strong>{china_beneficiary_count}</strong>
            <em>paper entries</em>
          </div>
          <div class="compare-metric multiplier" role="listitem">
            <span>Visibility shift</span>
            <strong>{benefit_multiplier:.0f}x</strong>
            <em>larger in the beneficiary layer</em>
          </div>
        </div>
        <p class="compare-note"><strong>Interpretation:</strong> China is not mainly showing up as the place where these papers were published. It shows up where platforms were scaled through manufacturing, supply chains, telecom deployment, cloud/data infrastructure, robotics, AI adoption, and domestic markets.</p>
      </section>
    """

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Billionaire Papers and Physical Intelligence: The Next Wave for Science</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #4b5563;
      --line: #cbd5e1;
      --origin: #2563eb;
      --value: #d97706;
      --china: #dc2626;
      --public: #2563eb;
      --private: #7c3aed;
      --mixed: #0f766e;
      --warn: #92400e;
      --warn-bg: #fff7ed;
      --success: #15803d;
      --success-bg: #f0fdf4;
      --shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.45;
    }}
    .skip-link {{
      position: absolute;
      left: 12px;
      top: -48px;
      z-index: 100;
      background: #ffffff;
      color: var(--ink);
      border: 2px solid var(--origin);
      border-radius: 6px;
      padding: 8px 10px;
    }}
    .skip-link:focus {{ top: 12px; }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 28px clamp(16px, 4vw, 48px) 18px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
    }}
    h2 {{ margin: 0 0 10px; font-size: 24px; letter-spacing: 0; }}
    h3 {{ margin: 18px 0 8px; font-size: 18px; letter-spacing: 0; }}
    p {{ margin: 0 0 12px; }}
    a {{ color: #0f5fa8; }}
    a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible {{
      outline: 3px solid #f59e0b;
      outline-offset: 3px;
    }}
    nav {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      gap: 8px;
      overflow-x: auto;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 10px clamp(16px, 4vw, 48px);
    }}
    nav a {{
      white-space: nowrap;
      text-decoration: none;
      color: var(--ink);
      padding: 8px 10px;
      border-radius: 6px;
      font-size: 14px;
    }}
    nav a:hover {{ background: #eef2f7; }}
    nav a:focus-visible {{ background: #dbeafe; }}
    main {{ padding: 22px clamp(16px, 4vw, 48px) 44px; }}
    section {{ margin: 0 0 32px; }}
    .subtitle {{ color: var(--muted); max-width: 1120px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin: 16px 0;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 14px;
      min-height: 86px;
    }}
    .metric.small {{ min-height: 62px; }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .metric strong {{
      display: block;
      font-size: 22px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr));
      gap: 16px;
      align-items: stretch;
    }}
    .chart {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 8px;
      min-height: 380px;
      overflow: hidden;
    }}
    .chart.thesis-chart {{
      min-height: 500px;
    }}
    .wide {{ grid-column: 1 / -1; }}
    .mode {{
      border-top: 4px solid var(--origin);
      padding-top: 18px;
    }}
    .mode.story {{ border-color: var(--china); }}
    .mode.thesis {{ border-color: var(--success); }}
    .pipeline {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 8px;
      margin: 16px 0;
    }}
    .pipeline span {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      font-weight: 700;
      text-align: center;
    }}
    .story-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 12px;
      margin: 16px 0;
    }}
    .story-card {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-left: 6px solid var(--origin);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 14px;
    }}
    .story-card.china {{ border-left-color: var(--china); }}
    .story-card.value {{ border-left-color: var(--value); }}
    .story-card.warning {{ border-left-color: var(--warn); background: var(--warn-bg); }}
    .thesis-flow {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 10px;
      margin: 16px 0;
    }}
    .thesis-flow span {{
      position: relative;
      background: #ffffff;
      border: 1px solid var(--line);
      border-left: 6px solid var(--success);
      border-radius: 8px;
      padding: 12px;
      min-height: 78px;
      font-weight: 800;
    }}
    .thesis-flow small {{
      display: block;
      color: var(--muted);
      font-weight: 600;
      margin-top: 4px;
    }}
    .thesis-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
      margin: 14px 0 18px;
    }}
    .thesis-card {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-left: 6px solid var(--mixed);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 14px;
    }}
    .thesis-card h3 {{
      margin-top: 0;
    }}
    .step {{
      display: inline-flex;
      width: 28px;
      height: 28px;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: #111827;
      color: #ffffff;
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .story-stat {{
      font-weight: 800;
      color: var(--ink);
      font-size: 18px;
    }}
    .china-compare {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-top: 6px solid var(--china);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: clamp(16px, 3vw, 28px);
      margin: 16px 0;
    }}
    .compare-head {{
      max-width: 980px;
      margin-bottom: 16px;
    }}
    .compare-head h3 {{
      margin-top: 0;
      font-size: clamp(22px, 3vw, 32px);
    }}
    .compare-row {{
      display: grid;
      grid-template-columns: minmax(180px, 1fr) auto minmax(180px, 1fr) minmax(180px, 0.8fr);
      gap: 14px;
      align-items: stretch;
    }}
    .compare-metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      background: #f8fafc;
      min-height: 150px;
    }}
    .compare-metric span,
    .compare-metric em {{
      display: block;
      color: var(--muted);
      font-style: normal;
    }}
    .compare-metric strong {{
      display: block;
      font-size: clamp(46px, 7vw, 82px);
      line-height: 0.95;
      margin: 10px 0;
    }}
    .compare-metric.origin {{
      border-left: 8px solid var(--origin);
    }}
    .compare-metric.china {{
      border-left: 8px solid var(--china);
      background: #fff7f7;
    }}
    .compare-metric.multiplier {{
      border-left: 8px solid var(--value);
      background: #fffbeb;
    }}
    .compare-arrow {{
      align-self: center;
      color: var(--muted);
      font-size: clamp(28px, 4vw, 52px);
      font-weight: 800;
      padding: 0 4px;
    }}
    .compare-note {{
      margin: 16px 0 0;
      max-width: 1180px;
    }}
    .revenue-capture {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-top: 6px solid var(--value);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: clamp(16px, 3vw, 28px);
      margin: 16px 0;
    }}
    .revenue-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
      margin-top: 14px;
    }}
    .revenue-card {{
      border: 1px solid var(--line);
      border-left: 8px solid var(--value);
      border-radius: 8px;
      background: #fffaf0;
      padding: 16px;
    }}
    .revenue-card.missing {{
      border-left-color: var(--warn);
      background: #fffbeb;
    }}
    .revenue-card.estimated {{
      border-left-color: var(--success);
      background: var(--success-bg);
    }}
    .revenue-card > span {{
      display: block;
      color: var(--muted);
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .revenue-card strong {{
      display: block;
      color: var(--ink);
      font-size: clamp(28px, 4vw, 44px);
      line-height: 1.05;
      overflow-wrap: anywhere;
    }}
    .revenue-card dl {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px 12px;
      margin: 12px 0;
    }}
    .revenue-card dt {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .revenue-card dd {{
      margin: 2px 0 0;
      font-weight: 800;
      overflow-wrap: anywhere;
    }}
    .revenue-note {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 0;
    }}
    .chart-summary {{
      margin: 0 0 8px;
      color: var(--muted);
      font-size: 14px;
    }}
    .callout {{
      background: #ecfeff;
      border: 1px solid #99f6e4;
      border-radius: 8px;
      padding: 14px;
      margin: 14px 0;
    }}
    .callout.warn {{ background: var(--warn-bg); border-color: #fed7aa; color: var(--warn); }}
    .callout.success {{ background: var(--success-bg); border-color: #86efac; color: #14532d; }}
    .controls {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin: 14px 0;
    }}
    .explorer-tabs {{
      display: inline-flex;
      gap: 4px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      padding: 4px;
      margin: 14px 0 4px;
    }}
    .tab-button {{
      border: 0;
      border-radius: 6px;
      background: transparent;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      font-weight: 800;
      min-height: 36px;
      padding: 8px 14px;
    }}
    .tab-button.active {{
      background: var(--origin);
      color: #ffffff;
    }}
    .explorer-panel[hidden] {{
      display: none;
    }}
    input, select {{
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 7px 9px;
      background: #ffffff;
      color: var(--ink);
    }}
    .table-wrap {{
      overflow: auto;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      max-height: 720px;
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
      font-size: 13px;
    }}
    .data-table th, .data-table td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
    }}
    .data-table th {{
      position: sticky;
      top: 0;
      background: #eef2f7;
      z-index: 1;
    }}
    .muted {{ color: var(--muted); }}
    .download-list {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }}
    .download-list a {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #ffffff;
      padding: 8px 10px;
      text-decoration: none;
    }}
    .case-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }}
    .case-card {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      box-shadow: var(--shadow);
    }}
    .case-card .badge {{
      display: inline-block;
      background: #e0f2fe;
      color: #075985;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      margin-bottom: 8px;
    }}
    .docs {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      max-height: 720px;
      overflow: auto;
    }}
    footer {{ color: var(--muted); padding: 24px clamp(16px, 4vw, 48px); border-top: 1px solid var(--line); }}
    @media (max-width: 880px) {{
      .compare-row {{
        grid-template-columns: 1fr;
      }}
      .compare-arrow {{
        transform: rotate(90deg);
        justify-self: center;
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
      }}
    }}
  </style>
</head>
<body>
  <div hidden aria-hidden="true">{plotly_loader}</div>
  <a class="skip-link" href="#main-content">Skip to dashboard content</a>
  <header role="banner">
    <h1>Billionaire Papers and Physical Intelligence: The Next Wave for Science</h1>
  </header>
  <nav aria-label="Dashboard sections">
    <a href="#story-mode">Story Mode</a>
    <a href="#physical-intelligence">Physical Intelligence</a>
    <a href="#physical-ai-companies">Company Landscape</a>
    <a href="#story-origin">Research Origin</a>
    <a href="#story-china">China Capture</a>
    <a href="#explorer-table">Dataset</a>
    <a href="#physical-ai-funding">Funding / Regions</a>
    <a href="#downloads">Downloads</a>
  </nav>
  <main id="main-content" tabindex="-1">
    <section id="story-mode" class="mode story" aria-labelledby="story-mode-title">
      <h2 id="story-mode-title">Story Mode</h2>
      <p class="subtitle">A guided, thesis-driven view: billionaire papers created the platform base; generative AI converted knowledge into models and predictions; Physical Intelligence is the next hypothesis to test for science acceleration.</p>
      <div class="pipeline" aria-label="Dashboard narrative sequence">
        <span>Billionaire papers</span>
        <span>Enabling platforms</span>
        <span>AI + robotics + simulation + automated labs</span>
        <span>Physical Intelligence companies</span>
        <span>Science acceleration</span>
        <span>Country value capture</span>
      </div>
      <div class="grid">{kpi_html}</div>
      <div class="callout warn">
        <strong>Read before interpreting:</strong>
        this dashboard treats Physical Intelligence as a thesis to support and stress-test, not as a settled forecast; estimates are models, not audited national accounts; papers usually enable markets rather than earning revenue directly; publication origin and value-capture country can differ; countries benefit through different roles; revenue, value added, profit proxy, cost savings, and consumer surplus are not interchangeable; the China layer is partial and not a complete country ranking.
      </div>
      <div class="story-grid" aria-label="Guided insight cards">
        {story_cards_html}
      </div>
    </section>

    <section id="physical-intelligence" class="mode thesis" aria-labelledby="physical-intelligence-title">
      <h2 id="physical-intelligence-title">Physical Intelligence Thesis</h2>
      <p class="subtitle">Physical Intelligence means AI systems that do not only reason or generate text, but also perceive, simulate, plan, manipulate, manufacture, synthesize, test, measure, and learn from the physical world.</p>
      <div class="thesis-flow" aria-label="Physical Intelligence transition sequence">
        <span>Billionaire papers<small>scientific and technical foundations</small></span>
        <span>Enabling platforms<small>batteries, semiconductors, solar, robotics, computer vision, AI for biology, cloud, molecular biology, automation, materials</small></span>
        <span>AI + robotics + simulation + automated labs<small>models connected to instruments, robots, factories, and experimental feedback</small></span>
        <span>Physical Intelligence companies<small>commercial systems that act, measure, and learn in physical workflows</small></span>
        <span>Science acceleration<small>biology, chemistry, materials, robotics, aerospace, energy, agriculture, manufacturing</small></span>
        <span>Strategic value capture<small>origin, IP, cloud, manufacturing, adoption, and evidence quality</small></span>
      </div>
      <div class="callout success">
        <strong>Thesis under test:</strong>
        the historical platform base is broad enough to make Physical Intelligence plausible as a next AI wave for science, but the evidence is not yet a revenue forecast. The weak links are deployment economics, lab and factory reliability, physical-data quality, regulatory pathways, and audited country-level value capture.
      </div>
      <h3>Company Archetypes To Watch</h3>
      <p class="chart-summary">These are categories of Physical Intelligence companies, not endorsements or forecasts for specific firms.</p>
      <div class="thesis-grid" aria-label="Physical Intelligence company archetypes">
        {thesis_company_cards_html}
      </div>
      <section id="physical-ai-companies" aria-labelledby="physical-ai-companies-title">
        <h3 id="physical-ai-companies-title">Active Physical AI Company Landscape</h3>
        <p class="subtitle">Active-only company dataset view: where Physical AI / Physical Intelligence companies are based, which sub-fields they occupy, and where disclosed or estimated investment has concentrated.</p>
        <div class="grid">{company_landscape_kpi_html}</div>
        <div class="callout warn">
          <strong>Investment caveat:</strong>
          funding estimates mix reported total funding, public-market proceeds, latest rounds, acquisition consideration, and range-based estimates. Treat totals as directional strategic signals, not audited capital accounts.
        </div>
        <div class="chart-grid">
          <section class="chart thesis-chart" aria-label="Active Physical AI companies by country">
            <p class="chart-summary"><strong>Country chart:</strong> active company-country exposures. Mixed-country companies are counted in each listed country for visibility.</p>
            {fig_html.get("physical_ai_country_counts", f'<p class="muted">Add {html.escape(PHYSICAL_AI_COMPANIES_CSV)} to render the country chart.</p>')}
          </section>
          <section class="chart thesis-chart" aria-label="Active Physical AI companies by sub-field">
            <p class="chart-summary"><strong>Sub-field chart:</strong> active companies grouped into intuitive Physical AI categories.</p>
            {fig_html.get("physical_ai_subfield_counts", f'<p class="muted">Add {html.escape(PHYSICAL_AI_COMPANIES_CSV)} to render the sub-field chart.</p>')}
          </section>
        </div>
      </section>
      <div class="chart-grid">
        <section class="chart thesis-chart" aria-label="Physical Intelligence capabilities chart">
          <p class="chart-summary"><strong>Capability chart:</strong> paper-linked Physical Intelligence capabilities, split by direct substrate, digital infrastructure, or adjacent platform relevance.</p>
          {fig_html.get("physical_intelligence_capabilities", '<p class="muted">Physical Intelligence capability chart appears after the thesis layer is built.</p>')}
        </section>
        <section class="chart thesis-chart" aria-label="Science acceleration domain chart">
          <p class="chart-summary"><strong>Domain chart:</strong> where the current platform base could accelerate science or physical industries.</p>
          {fig_html.get("physical_intelligence_domains", '<p class="muted">Science-domain chart appears after the thesis layer is built.</p>')}
        </section>
        <section class="chart wide" aria-label="Physical Intelligence platform capability domain Sankey">
          <p class="chart-summary"><strong>Platform → capability → domain Sankey:</strong> an auditable, rule-based view of how paper families connect to Physical Intelligence functions and science domains.</p>
          {fig_html.get("physical_intelligence_sankey", '<p class="muted">Physical Intelligence Sankey appears after the thesis layer is built.</p>')}
        </section>
      </div>
    </section>

    <section id="story-origin" class="mode" aria-labelledby="story-origin-title">
      <h2 id="story-origin-title">Where the Papers Came From</h2>
      <p class="chart-summary">Blue represents research origin. These charts count publication/research origin only, not later manufacturing, commercialization, or adoption.</p>
      <div class="chart-grid">
        <section class="chart" aria-label="Origin-country count map">
          <p class="chart-summary">Origin-country map: where papers originated.</p>
          {fig_html.get("origin_country_map", "")}
        </section>
        <section class="chart" aria-label="Research-origin country ranked bar chart">
          <p class="chart-summary">Ranked origin countries by number of papers.</p>
          {fig_html.get("origin_country_bar", "")}
        </section>
        <section class="chart" aria-label="Papers by field">
          <p class="chart-summary">Technology platforms and fields represented in the paper list.</p>
          {fig_html.get("broad_area", "")}
        </section>
      </div>
    </section>

    <section id="story-china" class="mode story" aria-labelledby="story-china-title">
      <h2 id="story-china-title">Why China Is Undercounted in Origin-Only Views</h2>
      <p class="subtitle">China appears in few research-origin rows, but the China benefit layer flags many papers where China plausibly captures value through manufacturing, supply chains, telecom, cloud/data platforms, robotics, AI adoption, and deployment markets.</p>
      <div class="grid">{china_kpi_html}</div>
      {china_comparison_html}
      {region_revenue_panel_html}
      <div class="chart-grid">
        <section class="chart wide" aria-label="Public private mixed research-origin institution chart">
          <p class="chart-summary"><strong>Public / private / mixed origin chart:</strong> papers grouped by the institution type at publication.</p>
          {fig_html.get("public_private", '<p class="muted">Public/private origin chart appears after the source CSV is loaded.</p>')}
        </section>
      </div>
      <div class="chart-grid">
        <section class="chart wide" aria-label="Origin platform China role Sankey">
          <p class="chart-summary"><strong>Origin → platform → China role Sankey:</strong> research origin flows into platforms and then China value-capture roles.</p>
          {fig_html.get("china_origin_platform_role_sankey", '<p class="muted">China role Sankey appears after the China update file is loaded.</p>')}
        </section>
        <section class="chart wide" aria-label="Origin platform US role Sankey">
          <p class="chart-summary"><strong>Origin → platform → US role Sankey:</strong> modeled assumption rows flowing into United States value-capture roles.</p>
          {fig_html.get("us_origin_platform_role_sankey", '<p class="muted">US role Sankey appears after US benefit assumption rows are loaded.</p>')}
        </section>
        <section class="chart wide" aria-label="Origin platform EU role Sankey">
          <p class="chart-summary"><strong>Origin → platform → EU role Sankey:</strong> modeled assumption rows flowing into EU member-country value-capture roles.</p>
          {fig_html.get("eu_origin_platform_role_sankey", '<p class="muted">EU role Sankey appears after EU benefit assumption rows are loaded.</p>')}
        </section>
      </div>
    </section>

    <section id="explorer-table" aria-labelledby="explorer-table-title">
      <h2 id="explorer-table-title">Data Explorer</h2>
      <p class="subtitle">Search papers and active Physical AI companies from one place. Use the tabs to switch between the research-origin dataset and the company landscape dataset.</p>
      <div class="explorer-tabs" role="tablist" aria-label="Data explorer datasets">
        <button class="tab-button active" id="papers-tab" type="button" role="tab" aria-selected="true" aria-controls="papers-panel" data-tab="papers">Papers</button>
        <button class="tab-button" id="companies-tab" type="button" role="tab" aria-selected="false" aria-controls="companies-panel" data-tab="companies">Companies</button>
      </div>
      <div class="controls" aria-label="Shared data explorer search">
        <input id="search-box" type="search" aria-label="Search papers and companies" placeholder="Search papers, companies, countries, fields, institutions, rationales, funding notes">
      </div>
      <section id="papers-panel" class="explorer-panel" role="tabpanel" aria-labelledby="papers-tab">
        <h3>Papers</h3>
        <p class="chart-summary">Search paper titles, authors, institutions, countries, DOI links, and platform fields.</p>
        <div class="controls" aria-label="Paper dataset filters">
          <select id="confidence-filter" aria-label="Filter papers by confidence tier">{build_filter_options(cleaned["confidence_tier_clean"])}</select>
          <select id="area-filter" aria-label="Filter papers by broad area">{build_filter_options(cleaned["broad_area_clean"])}</select>
          <select id="origin-filter" aria-label="Filter papers by origin country">{build_filter_options(origin_long["origin_country"])}</select>
          <select id="public-filter" aria-label="Filter papers by public or private origin">{build_filter_options(cleaned["public_private_clean"])}</select>
        </div>
        <div class="table-wrap">{explorer_table}</div>
      </section>
      <section id="companies-panel" class="explorer-panel" role="tabpanel" aria-labelledby="companies-tab" hidden>
        <h3>Companies</h3>
        <p class="chart-summary">Search active company names, countries, strategic regions, sub-fields, Physical AI use cases, investment notes, and source links.</p>
        <div class="controls" aria-label="Company dataset filters">
          <select id="company-region-filter" aria-label="Filter companies by strategic region">{company_filter_options["region"]}</select>
          <select id="company-country-filter" aria-label="Filter companies by country">{build_filter_options(physical_ai_country_summary["country"] if not physical_ai_country_summary.empty else pd.Series(dtype=str))}</select>
          <select id="company-subfield-filter" aria-label="Filter companies by sub-field">{company_filter_options["subfield"]}</select>
          <select id="company-status-filter" aria-label="Filter companies by active status">{company_filter_options["status"]}</select>
          <select id="company-confidence-filter" aria-label="Filter companies by investment evidence confidence">{company_filter_options["confidence"]}</select>
          <select id="company-caution-filter" aria-label="Filter companies by funding metric caution">
            <option value="">All</option>
            <option value="yes">Has funding caution</option>
            <option value="no">No funding caution</option>
          </select>
        </div>
        <div class="table-wrap">{company_explorer_table}</div>
      </section>
    </section>

    <section id="physical-ai-funding" class="mode thesis" aria-labelledby="physical-ai-funding-title">
      <h2 id="physical-ai-funding-title">Physical AI Funding and Strategic Regions</h2>
      <p class="subtitle">The company count view shows where the ecosystem exists; these charts show where estimated capital has concentrated and how that compares across strategic regions.</p>
      <div class="callout warn">
        <strong>Read before comparing funding:</strong>
        estimates mix reported total funding, public-market proceeds, latest rounds, acquisition consideration, and range-based estimates. Use this section as a strategic landscape view, not audited investment accounting.
      </div>
      <div class="chart-grid">
        <section class="chart wide thesis-chart" aria-label="Physical AI funding by sub-field">
          <p class="chart-summary"><strong>Funding by sub-field:</strong> base investment estimate in USD billions, with low/high uncertainty bands where available.</p>
          {fig_html.get("physical_ai_subfield_funding", f'<p class="muted">Add {html.escape(PHYSICAL_AI_COMPANIES_CSV)} to render the funding chart.</p>')}
        </section>
        <section class="chart wide thesis-chart" aria-label="Strategic region comparison for Physical AI companies">
          <p class="chart-summary"><strong>Strategic region comparison:</strong> x-axis is active company count; y-axis is base investment estimate. Cross-region companies are bucketed as Other / mixed.</p>
          {fig_html.get("physical_ai_region_bubble", f'<p class="muted">Add {html.escape(PHYSICAL_AI_COMPANIES_CSV)} to render the strategic-region comparison.</p>')}
        </section>
      </div>
    </section>

    <section id="downloads" aria-labelledby="downloads-title">
      <h2 id="downloads-title">Download Files</h2>
      <p class="subtitle">These links work when the HTML is opened from the same directory as the generated artifacts.</p>
      <div class="download-list">
        <a href="{input_csv_path}">Source CSV</a>
        <a href="{ASSUMPTIONS_CSV}">Assumptions template</a>
        <a href="{CHINA_BENEFIT_LONG_CSV}">China benefit long table</a>
        <a href="{CHINA_SUMMARY_CSV}">China summary</a>
        <a href="{BENEFIT_ESTIMATES_CSV}">Benefit estimates</a>
        <a href="{BENEFIT_LONG_CSV}">Benefit long table</a>
        <a href="{COUNTRY_SUMMARY_CSV}">Country summary</a>
        <a href="{ORIGIN_COUNTRY_SUMMARY_CSV}">Origin country summary</a>
        <a href="{ORIGIN_TO_BENEFICIARY_FLOW_CSV}">Origin-beneficiary flows</a>
        <a href="{FIELD_COUNTRY_SUMMARY_CSV}">Field-country summary</a>
        <a href="{PUBLIC_PRIVATE_SPILLOVER_SUMMARY_CSV}">Public/private spillover</a>
        <a href="{PHYSICAL_INTELLIGENCE_LINKS_CSV}">Physical Intelligence thesis links</a>
        <a href="{PHYSICAL_INTELLIGENCE_DOMAIN_SUMMARY_CSV}">Physical Intelligence domain summary</a>
        <a href="{PHYSICAL_AI_COMPANIES_CSV}">Active Physical AI companies source</a>
        <a href="{PHYSICAL_AI_COMPANIES_CLEAN_CSV}">Active Physical AI companies clean</a>
        <a href="{PHYSICAL_AI_COUNTRY_SUMMARY_CSV}">Physical AI country summary</a>
        <a href="{PHYSICAL_AI_SUBFIELD_SUMMARY_CSV}">Physical AI sub-field summary</a>
        <a href="{PHYSICAL_AI_REGION_SUMMARY_CSV}">Physical AI region summary</a>
        <a href="{QUALITY_CHECK_REPORT_CSV}">Quality report</a>
        <a href="{INSTRUCTIONS_MD}">Dashboard instructions</a>
        <a href="{OUTPUT_NOTEBOOK}">Colab notebook</a>
        <a href="{REQUIREMENTS_TXT}">Requirements</a>
      </div>
    </section>
  </main>
  <footer>
    Revenue is not profit. Gross exports can overstate true value added. Every monetary estimate should be treated as provisional until audited against cited evidence.
  </footer>
  <script>
    function getActiveExplorerTab() {{
      const activeButton = document.querySelector('.tab-button.active');
      return activeButton ? activeButton.dataset.tab : 'papers';
    }}
    function setExplorerTab(tab) {{
      document.querySelectorAll('.tab-button').forEach(button => {{
        const selected = button.dataset.tab === tab;
        button.classList.toggle('active', selected);
        button.setAttribute('aria-selected', selected ? 'true' : 'false');
      }});
      document.querySelectorAll('.explorer-panel').forEach(panel => {{
        panel.hidden = panel.id !== `${{tab}}-panel`;
      }});
      filterTable();
    }}
    function filterTable() {{
      const search = document.getElementById('search-box').value.toLowerCase();
      const activeTab = getActiveExplorerTab();
      if (activeTab === 'papers') {{
      const confidence = document.getElementById('confidence-filter').value;
      const area = document.getElementById('area-filter').value;
      const origin = document.getElementById('origin-filter').value;
      const pub = document.getElementById('public-filter').value;
      document.querySelectorAll('#papers-table tbody tr').forEach(row => {{
        const text = row.innerText.toLowerCase();
        const okSearch = !search || text.includes(search);
        const okConf = !confidence || row.dataset.confidence === confidence;
        const okArea = !area || row.dataset.area === area;
        const okOrigin = !origin || (row.dataset.origin || '').split('; ').includes(origin);
        const okPub = !pub || row.dataset.publicprivate === pub;
        row.style.display = (okSearch && okConf && okArea && okOrigin && okPub) ? '' : 'none';
      }});
      }} else {{
        const region = document.getElementById('company-region-filter').value;
        const country = document.getElementById('company-country-filter').value;
        const subfield = document.getElementById('company-subfield-filter').value;
        const status = document.getElementById('company-status-filter').value;
        const confidence = document.getElementById('company-confidence-filter').value;
        const caution = document.getElementById('company-caution-filter').value;
        document.querySelectorAll('#companies-table tbody tr').forEach(row => {{
          const text = row.innerText.toLowerCase();
          const countries = (row.dataset.country || '').split('; ').map(value => value.trim());
          const okSearch = !search || text.includes(search);
          const okRegion = !region || row.dataset.region === region;
          const okCountry = !country || countries.includes(country);
          const okSubfield = !subfield || row.dataset.subfield === subfield;
          const okStatus = !status || row.dataset.status === status;
          const okConfidence = !confidence || row.dataset.confidence === confidence;
          const okCaution = !caution || row.dataset.caution === caution;
          row.style.display = (okSearch && okRegion && okCountry && okSubfield && okStatus && okConfidence && okCaution) ? '' : 'none';
        }});
      }}
    }}
    document.querySelectorAll('.tab-button').forEach(button => {{
      button.addEventListener('click', () => setExplorerTab(button.dataset.tab));
    }});
    [
      'search-box',
      'confidence-filter',
      'area-filter',
      'origin-filter',
      'public-filter',
      'company-region-filter',
      'company-country-filter',
      'company-subfield-filter',
      'company-status-filter',
      'company-confidence-filter',
      'company-caution-filter'
    ].forEach(id => {{
      document.getElementById(id).addEventListener('input', filterTable);
      document.getElementById(id).addEventListener('change', filterTable);
    }});
  </script>
</body>
</html>
"""
    Path(output_path).write_text(html_text, encoding="utf-8")


def build_case_study_cards(cleaned: pd.DataFrame, benefit_estimates: pd.DataFrame) -> str:
    cards = []
    for label, keywords in CASE_STUDY_KEYWORDS:
        mask = pd.Series(False, index=cleaned.index)
        for keyword in keywords:
            pattern = re.escape(keyword)
            mask = mask | cleaned["Paper_or_discovery"].str.contains(pattern, case=False, na=False)
            mask = mask | cleaned["Field_or_platform"].str.contains(pattern, case=False, na=False)
        matches = cleaned[mask]
        if matches.empty:
            cards.append(
                f"""
                <article class="case-card">
                  <span class="badge">Data gap</span>
                  <h3>{html.escape(label)}</h3>
                  <p class="muted">No matching source row found. Add or tag this case in the source CSV.</p>
                </article>
                """
            )
            continue
        row = matches.iloc[0]
        estimates = benefit_estimates[benefit_estimates["paper_id"].eq(row["paper_id"])] if not benefit_estimates.empty else pd.DataFrame()
        countries = "; ".join(sorted(estimates["beneficiary_country"].dropna().unique())) if not estimates.empty else "Not assigned"
        roles = "; ".join(sorted(estimates["beneficiary_role"].dropna().unique())) if not estimates.empty else "Not assigned"
        revenue = estimates["revenue_capture_base_usd"].sum(min_count=1) if not estimates.empty else np.nan
        profit = estimates["profit_proxy_base_usd"].sum(min_count=1) if not estimates.empty else np.nan
        cards.append(
            f"""
            <article class="case-card">
              <span class="badge">{html.escape(clean_text(row["confidence_tier_clean"]))}</span>
              <h3>{html.escape(label)}</h3>
              <p><strong>Paper/platform:</strong> {html.escape(clean_text(row["Paper_or_discovery"]))}</p>
              <p><strong>Origin:</strong> {html.escape(clean_text(row["Institution_at_publication"]))}; {html.escape(clean_text(row["origin_country_list"]))}</p>
              <p><strong>Main link:</strong> {linkify(clean_text(row["DOI_or_link"]))}</p>
              <p><strong>Enabled market/product class:</strong> {html.escape(clean_text(row["Field_or_platform"]))}</p>
              <p><strong>Beneficiary countries:</strong> {html.escape(countries)}</p>
              <p><strong>Roles:</strong> {html.escape(roles)}</p>
              <p><strong>Base revenue capture:</strong> {format_usd(revenue)}; <strong>base profit proxy:</strong> {format_usd(profit)}</p>
              <p><strong>Open questions:</strong> audited enabled market size, paper attribution factor, country role shares, value-added versus gross revenue, margin assumptions.</p>
            </article>
            """
        )
    return "\n".join(cards)


def build_case_study_table(cleaned: pd.DataFrame, benefit_estimates: pd.DataFrame) -> str:
    rows = []
    for label, keywords in CASE_STUDY_KEYWORDS:
        mask = pd.Series(False, index=cleaned.index)
        for keyword in keywords:
            pattern = re.escape(keyword)
            mask = mask | cleaned["Paper_or_discovery"].str.contains(pattern, case=False, na=False)
            mask = mask | cleaned["Field_or_platform"].str.contains(pattern, case=False, na=False)
        matches = cleaned[mask]
        if matches.empty:
            rows.append(
                {
                    "case_study": label,
                    "paper_id": "",
                    "origin": "",
                    "field_or_platform": "",
                    "assumption_rows": 0,
                    "status": "Missing source row",
                }
            )
            continue
        row = matches.iloc[0]
        estimates = benefit_estimates[benefit_estimates["paper_id"].eq(row["paper_id"])] if not benefit_estimates.empty else pd.DataFrame()
        status = "Needs audited economic assumptions"
        if not estimates.empty and estimates["revenue_capture_base_usd"].notna().any():
            status = "Has value estimates"
        rows.append(
            {
                "case_study": label,
                "paper_id": int(row["paper_id"]),
                "origin": clean_text(row["origin_country_list"]),
                "field_or_platform": clean_text(row["Field_or_platform"]),
                "assumption_rows": len(estimates),
                "status": status,
            }
        )
    return dataframe_to_html_table(pd.DataFrame(rows), "case-study-table")


def linkify(text: str) -> str:
    if not text:
        return ""
    first = text.split(";")[0].strip()
    if first.startswith("http"):
        return f'<a href="{html.escape(first)}">{html.escape(first)}</a>'
    return html.escape(text)


def markdown_to_simple_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    out = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_table:
                out.append("</tbody></table>")
                in_table = False
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            parts = [html.escape(p.strip()) for p in stripped.strip("|").split("|")]
            is_sep = all(set(p) <= {"-", ":"} for p in parts)
            if is_sep:
                continue
            if not in_table:
                out.append('<table class="data-table"><tbody>')
                in_table = True
            out.append("<tr>" + "".join(f"<td>{p}</td>" for p in parts) + "</tr>")
            continue
        if in_table:
            out.append("</tbody></table>")
            in_table = False
        if stripped.startswith("# "):
            out.append(f"<h2>{html.escape(stripped[2:])}</h2>")
        elif stripped.startswith("## "):
            out.append(f"<h3>{html.escape(stripped[3:])}</h3>")
        elif stripped.startswith("- "):
            out.append(f"<p>&bull; {html.escape(stripped[2:])}</p>")
        else:
            out.append(f"<p>{html.escape(stripped)}</p>")
    if in_table:
        out.append("</tbody></table>")
    return "\n".join(out)


def write_requirements(path: str | Path = REQUIREMENTS_TXT) -> None:
    requirements = "\n".join(
        [
            "pandas",
            "numpy",
            "plotly",
            "pycountry",
            "country_converter",
            "scipy",
            "nbformat",
            "ipywidgets",
            "kaleido",
            "openpyxl",
            "",
        ]
    )
    Path(path).write_text(requirements, encoding="utf-8")


def write_instructions(path: str | Path = INSTRUCTIONS_MD) -> str:
    today = date.today().isoformat()
    text = dedent(
        f"""
        ---
        methodology_version: 0.4.0
        last_updated: {today}
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
        | {today} | Reframed the dashboard around the Physical Intelligence thesis, added thesis-link CSVs, and kept country value capture as a stress-test layer. | Codex | User requested a thesis-driven presentation about the next AI wave for science. | Notebook, HTML, CSV outputs, Markdown guide |
        """
    ).strip() + "\n"
    Path(path).write_text(text, encoding="utf-8")
    return text


def notebook_code() -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    # The Colab notebook should be self-contained and rerunnable.
    source = re.sub(r"\nif __name__ == \"__main__\":\n    main\(\)\n\Z", "", source)
    source += dedent(
        """

        # Run the full local/Colab build.
        main(write_notebook_output=False)
        """
    )
    return source


def write_notebook(path: str | Path = OUTPUT_NOTEBOOK) -> None:
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        "colab": {"name": OUTPUT_NOTEBOOK, "provenance": []},
    }
    cells = [
        nbf.v4.new_markdown_cell(
            "# Billionaire Papers and Physical Intelligence: The Next Wave for Science\n\n"
            "This Colab notebook builds a standalone interactive HTML dashboard from the billionaire-papers CSV. "
            "It frames Physical Intelligence as a thesis to support and stress-test, then exports the thesis layer, "
            "country value-capture assumptions, summary CSVs, and the standalone presentation HTML."
        ),
        nbf.v4.new_markdown_cell("## 1. Project overview\n\nThe workflow validates the source schema, normalizes country names, classifies paper-to-Physical-Intelligence thesis links, separates research origin from economic value capture, creates starter assumptions, calculates low/base/high estimates when numeric assumptions are present, and exports a standalone HTML dashboard."),
        nbf.v4.new_markdown_cell("## 2. Install/import packages\n\nRun this cell in Colab if packages are missing. The local build uses already installed packages when available."),
        nbf.v4.new_code_cell(
            dedent(
                """
                import importlib.util
                import sys
                import subprocess

                needed = ["pandas", "numpy", "plotly", "nbformat"]
                missing = [pkg for pkg in needed if importlib.util.find_spec(pkg) is None]
                optional = ["pycountry", "country_converter", "scipy", "ipywidgets", "kaleido", "openpyxl"]
                missing_optional = [pkg for pkg in optional if importlib.util.find_spec(pkg) is None]
                if "google.colab" in sys.modules and (missing or missing_optional):
                    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, *missing_optional])
                print("Package check complete")
                """
            )
        ),
        nbf.v4.new_markdown_cell("## 3-14. Reproducible dashboard build\n\nThe cell below contains the complete build logic. It supports Colab upload if the source CSV is not already present."),
        nbf.v4.new_code_cell(
            dedent(
                """
                from pathlib import Path
                import sys

                source_files = [
                    "billionaire_papers_1976_2026_china_benefit_updated.csv",
                    "billionaire_papers_1976_2026.csv",
                ]
                if "google.colab" in sys.modules and not any(Path(path).exists() for path in source_files):
                    from google.colab import files
                    uploaded = files.upload()
                    if not any(path in uploaded for path in source_files):
                        raise FileNotFoundError(
                            "Please upload billionaire_papers_1976_2026_china_benefit_updated.csv "
                            "or billionaire_papers_1976_2026.csv"
                        )
                """
            )
        ),
        nbf.v4.new_code_cell(notebook_code()),
        nbf.v4.new_markdown_cell(
            "## How to update the model\n\n"
            "Edit `paper_benefit_assumptions_template.csv`, then rerun the notebook. "
            "The dashboard will update country value-capture maps, rankings, uncertainty intervals, and summaries once numeric revenue, attribution, share, and margin fields are populated with cited assumptions."
        ),
    ]
    nb["cells"] = cells
    nbf.write(nb, path)


def main(write_notebook_output: bool = True) -> None:
    input_csv_path = select_input_csv()
    df = load_source_csv(input_csv_path)
    cleaned, origin_long = clean_papers(df)
    quality_checks = make_quality_checks(cleaned, origin_long)
    china_update = load_china_benefit_update(CHINA_BENEFIT_LONG_CSV)
    china_summary = build_china_summary(china_update)
    assumptions = create_assumptions_template(cleaned)
    assumptions = add_china_update_to_assumptions(assumptions, china_update)
    assumption_warnings = validate_assumptions(assumptions)
    benefit_estimates, benefit_long = calculate_country_benefit(assumptions, cleaned)
    country_summary = aggregate_country_summary(benefit_estimates, cleaned, origin_long)
    origin_country_summary = build_origin_country_summary(origin_long, cleaned)
    origin_to_beneficiary_flow = build_origin_to_beneficiary_flow(china_update, origin_long)
    field_country_summary = build_field_country_summary(origin_to_beneficiary_flow)
    public_private_spillover_summary = build_public_private_spillover_summary(origin_to_beneficiary_flow, cleaned)
    physical_intelligence_links = build_physical_intelligence_links(cleaned)
    physical_intelligence_domain_summary = build_physical_intelligence_domain_summary(physical_intelligence_links)
    physical_ai_companies_raw = load_physical_ai_companies(PHYSICAL_AI_COMPANIES_CSV)
    (
        physical_ai_companies_clean,
        physical_ai_country_summary,
        physical_ai_subfield_summary,
        physical_ai_region_summary,
    ) = build_physical_ai_company_tables(physical_ai_companies_raw)
    quality_check_report = build_quality_check_report(
        quality_checks=quality_checks,
        assumption_warnings=assumption_warnings,
        cleaned=cleaned,
        china_update=china_update,
        flow_df=origin_to_beneficiary_flow,
    )

    assumptions.to_csv(ASSUMPTIONS_CSV, index=False)
    benefit_estimates.to_csv(BENEFIT_ESTIMATES_CSV, index=False)
    origin_to_beneficiary_flow.to_csv(BENEFIT_LONG_CSV, index=False)
    country_summary.to_csv(COUNTRY_SUMMARY_CSV, index=False)
    china_summary.to_csv(CHINA_SUMMARY_CSV, index=False)
    origin_country_summary.to_csv(ORIGIN_COUNTRY_SUMMARY_CSV, index=False)
    origin_to_beneficiary_flow.to_csv(ORIGIN_TO_BENEFICIARY_FLOW_CSV, index=False)
    field_country_summary.to_csv(FIELD_COUNTRY_SUMMARY_CSV, index=False)
    public_private_spillover_summary.to_csv(PUBLIC_PRIVATE_SPILLOVER_SUMMARY_CSV, index=False)
    physical_intelligence_links.to_csv(PHYSICAL_INTELLIGENCE_LINKS_CSV, index=False)
    physical_intelligence_domain_summary.to_csv(PHYSICAL_INTELLIGENCE_DOMAIN_SUMMARY_CSV, index=False)
    physical_ai_companies_clean.to_csv(PHYSICAL_AI_COMPANIES_CLEAN_CSV, index=False)
    physical_ai_country_summary.to_csv(PHYSICAL_AI_COUNTRY_SUMMARY_CSV, index=False)
    physical_ai_subfield_summary.to_csv(PHYSICAL_AI_SUBFIELD_SUMMARY_CSV, index=False)
    physical_ai_region_summary.to_csv(PHYSICAL_AI_REGION_SUMMARY_CSV, index=False)
    quality_check_report.to_csv(QUALITY_CHECK_REPORT_CSV, index=False)
    write_requirements(REQUIREMENTS_TXT)
    instructions_md = write_instructions(INSTRUCTIONS_MD)
    write_dashboard_html(
        cleaned=cleaned,
        origin_long=origin_long,
        assumptions=assumptions,
        benefit_estimates=benefit_estimates,
        country_summary=country_summary,
        china_update=china_update,
        china_summary=china_summary,
        origin_country_summary=origin_country_summary,
        origin_to_beneficiary_flow=origin_to_beneficiary_flow,
        field_country_summary=field_country_summary,
        public_private_spillover_summary=public_private_spillover_summary,
        quality_check_report=quality_check_report,
        physical_intelligence_links=physical_intelligence_links,
        physical_intelligence_domain_summary=physical_intelligence_domain_summary,
        physical_ai_companies_clean=physical_ai_companies_clean,
        physical_ai_country_summary=physical_ai_country_summary,
        physical_ai_subfield_summary=physical_ai_subfield_summary,
        physical_ai_region_summary=physical_ai_region_summary,
        quality_checks=quality_checks,
        assumption_warnings=assumption_warnings,
        instructions_md=instructions_md,
        input_csv_path=input_csv_path,
        output_path=OUTPUT_HTML,
    )
    if write_notebook_output:
        write_notebook(OUTPUT_NOTEBOOK)

    print(f"Loaded {len(cleaned)} papers from {input_csv_path}")
    if write_notebook_output:
        print(f"Wrote {OUTPUT_HTML}, {OUTPUT_NOTEBOOK}, {INSTRUCTIONS_MD}, and CSV outputs")
    else:
        print(f"Wrote {OUTPUT_HTML}, {INSTRUCTIONS_MD}, and CSV outputs")


if __name__ == "__main__":
    main()
