# README — Windows-APT 2025 Scenario-Mapping Supplement (v4)

This document describes the v4 supplement to the *Windows-APT 2025* dataset —
Mozaffari, Yazdinejad, Dehghantanha, *Data in Brief* 65 (2026) 112569;
Mendeley DOI [10.17632/b8fmtzvpy8.3](https://data.mendeley.com/datasets/b8fmtzvpy8/3).

---

## What this supplement adds

This supplement provides an optional derived row-level scenario mapping for analyses that benefit from scenario context, covering all 102,011 log rows. Each row receives a derived `Scenario_ID`, a posterior confidence distribution over the 36 scenarios, and an evidence trace.

**All v3 files are unchanged.** The 16 per-period log CSVs, the combined log CSV, `scenario_manifest.csv`, and `validation_summary.csv` are untouched. The SHA-256 checksums published with v3 remain valid.

---

## Using attribution-strength tiers

Each row is assigned one of four attribution-strength tiers based on how decisively the evidence supports a single scenario:

| Tier | Meaning |
|---|---|
| `UNIQUE-MATCH` | Strong evidence supports a single scenario, with a clear separation from all alternatives. |
| `NARROWED` | One scenario is favored, with good supporting evidence and a positive margin. |
| `SHARED-WEAK` | One scenario leads the posterior, suitable as a soft or auxiliary label. |
| `UNRESOLVED` | Insufficient technique signal; `Scenario_ID` is left empty. |

For highest-confidence scenario labels, restrict to `Attribution_Strength IN ('UNIQUE-MATCH', 'NARROWED')`. `SHARED-WEAK` rows are well-suited for soft or exploratory analysis.

**`Derived_Label` values** indicate how each row's MITRE technique tag relates to its assigned scenario:

| Derived_Label | Meaning |
|---|---|
| `technique-tagged` | MITRE technique tag is in the assigned scenario's expected set |
| `technique-unmatched` | Row has a technique tag not in the assigned scenario's set (assignment came from episode context) |
| `untagged` | No MITRE technique tag present (may be benign baseline, evasion, or missed detection) |
| `NA` | Technique-tagged but scenario is UNRESOLVED (no assignment made) |

---

## Data-leakage note

`Scenario_ID` is derived from each row's MITRE technique tag. For any model that also uses the technique field as a feature, use the scenario label as a stratification or grouping variable rather than as an independent evaluation target, to avoid circularity.

---

## Files in this supplement

| File | Purpose |
|---|---|
| `README_supplement_v4.md` | This file. |
| `build_scenario_mapping_v4.py` | The v4 attribution engine (Python stdlib only; no third-party dependencies). Run `--selftest` for internal sanity checks. |
| `scenario_mapping_walkthrough.ipynb` | Notebook walkthrough with diagnostics and visualisations, including a hard-argmax-vs-soft-mass comparison chart. |
| `log_to_scenario_mapping.csv` | Row-level output: `Scenario_ID`, `Scenario_Name`, `MITRE_Group_ID`, `Scenario_Posterior`, `Derived_Label`, `Attribution_Strength`, `Mapping_Evidence`, `Candidate_Scenarios`. |

SHA-256 of `log_to_scenario_mapping.csv`: `A2B7751838CA973992427835D7EAB4DEE269E14CD0D2FCFB4ECC5CCF7E637E98`

---

## How to use

Place this supplement next to the released Windows-APT 2025 CSVs (or use it in-place as the `scenario_mapping_supplement/` subfolder of the unzipped release), then run the pipeline:

```bash
python build_scenario_mapping_v4.py \
    --data-dir "<folder with released CSVs>" \
    --out-dir  "<this supplement folder>" \
    --verbose
```

Or open the notebook and run all cells:

```bash
jupyter notebook scenario_mapping_walkthrough.ipynb
```

For a scenario-aware analysis, join your log rows to `log_to_scenario_mapping.csv` on `(Source_CSV, Row_Index)`. Prefer the `Scenario_Posterior` distribution over the single `Scenario_ID` when possible; if you need a hard label, restrict to `Attribution_Strength IN ('UNIQUE-MATCH', 'NARROWED')`. Before treating any rows from S02, S04, S12, S13, or S22 as uniquely theirs, check the `Subset_masked_by` column in `log_to_scenario_mapping.csv` — these five scenarios share techniques with larger scenarios and their rows are best addressed through the soft posterior.

---

## Agent-name note

The agent name `Maryam` appearing in the released logs identifies the Wazuh management host, not an attack-simulation endpoint. Events from agent `Maryam` are predominantly `untagged` and represent Wazuh infrastructure telemetry. They should be treated as benign baseline activity.

---

## Citation

If you use this supplement in published work, please cite the original dataset and paper (Mozaffari, Yazdinejad, Dehghantanha, 2026) and note that the row-level scenario-mapping was derived post-hoc via the companion pipeline in this directory.
