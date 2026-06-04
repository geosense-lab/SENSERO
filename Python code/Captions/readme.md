# SENSERO Metadata Preparation Workflow

This repository contains the preprocessing and metadata generation workflow used for the SENSERO dataset.

The pipeline consists of four major stages:

1. Generate all caption variants
2. Create dataset splits
3. Enforce geographic separation to reduce spatial leakage
4. Merge all metadata into final Parquet files

---

# 1. Generate Caption Metadata

Run all five caption generation notebooks.

These notebooks create different semantic caption variants that are later merged into the final metadata tables.

## Required notebooks

- `caption_bigearthnet.ipynb`
- `caption_clc_level1.ipynb`
- `caption_clc_level2.ipynb`
- `caption_clc_level3.ipynb`
- `caption_custom.ipynb`

## Output

The notebooks generate intermediate CSV metadata files containing:

- CORINE Land Cover labels
- hierarchical captions
- BigEarthNet-style labels
- custom captions
- semantic descriptors

These outputs are later consumed by the split and merge stages.

---

# 2. Generate Dataset Splits

Run:

- `dataset_split.ipynb`

## Requirements

This step requires:

- `clc_legend.csv`

The split generation workflow performs:

- multilabel stratification
- TRAIN / VAL / TEST assignment
- class balance preservation
- rare class handling

## Output

Typical outputs include:

- split CSV files
- split statistics
- class distribution summaries

---

# 3. Enforce Geographic Separation

Run:

- `train_eval_leakage_enforcement.ipynb`

This stage reduces geographic leakage between TRAIN, VAL, and TEST subsets.

The workflow analyzes patch proximity and overlap relationships to prevent spatially adjacent samples from appearing in different splits.

## Input

Use the CSV overlap/leakage reports generated during preprocessing.

Typical reports contain:

- overlapping patch pairs
- centroid distances
- IoU / overlap statistics
- split conflicts

## Purpose

This stage improves evaluation reliability by reducing:

- spatial autocorrelation
- train-test contamination
- geographic information leakage

## Output

The workflow generates:

- corrected split assignments
- leakage enforcement reports
- updated metadata tables

---

# 4. Merge Final Metadata

Run:

- `merge_metadata.ipynb`

This notebook merges all generated metadata into consolidated Parquet files.

The merge process combines:

- captions
- split assignments
- geographic metadata
- CLC labels
- auxiliary descriptors
- patch metadata

## Output

Final outputs include:

- `metadata_64.parquet`
- `metadata_112.parquet`
- `metadata_128.parquet`
- `metadata_224.parquet`
- `metadata_336.parquet`

(depending on the generated patch sizes)

These Parquet files represent the final metadata tables used for:

- training
- evaluation
- retrieval
- captioning
- RAG workflows
- dataset publication

---

# Recommended Execution Order

Run notebooks in the following order:

1. Caption notebooks
2. `dataset_split.ipynb`
3. `train_eval_leakage_enforcement.ipynb`
4. `merge_metadata.ipynb`

---

# Notes

- Geographic leakage enforcement should always be performed after initial split generation.
- Any patch removal or overlap correction requires regenerating the metadata tables.
