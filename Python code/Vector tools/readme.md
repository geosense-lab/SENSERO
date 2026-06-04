# SENSERO Spatial Metadata Preparation Workflow

This repository contains the workflows used to generate and maintain the spatial metadata layers associated with the SENSERO dataset.

The pipeline includes:

1. Convert shapefiles to Parquet metadata
2. Create the dataset GeoPackage
3. Update and synchronize the GeoPackage

---

# 1. Convert Shapefiles to Parquet Metadata

Run:

- `shp2parquet.ipynb`

This notebook converts vector spatial metadata into Parquet format for efficient downstream processing.

## Purpose

The workflow is used to:

- read shapefiles containing patch metadata
- extract spatial and attribute information
- standardize metadata fields
- generate compact Parquet tables

## Typical Inputs

- ESRI Shapefiles (`.shp`)
- associated `.dbf`, `.shx`, and projection files

## Output

Typical outputs include:

- metadata Parquet files
- spatial coordinate tables
- patch geometry metadata
- centroid information

---

# 2. Create Dataset GeoPackage

Run:

- `create_dataset_geopackage.ipynb`

This notebook generates the master GeoPackage containing the spatial representation of the dataset.

## Purpose

The workflow creates:

- patch polygons
- centroids
- spatial metadata layers
- visualization-ready GIS layers

The GeoPackage can be used in:

- QGIS
- ArcGIS
- geopandas workflows
- overlap analysis
- geographic inspection
- quality control

## Included Information

Typical attributes include:

- patch identifiers
- split assignments
- CLC labels
- caption metadata
- geographic coordinates

---

# Recommended Execution Order

Run notebooks in the following order:

1. `shp2parquet.ipynb` - you need this after selecting patches in QGIS and before extracting patches
2. `create_dataset_geopackage.ipynb` - run after extracting all patches
3. `update_dataset_geopackage.ipynb` - run after creating metadata - (adds train - val - test attribute)

---
