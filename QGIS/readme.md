# QGIS Scripts

This folder contains Python scripts developed for **QGIS** automation and geospatial data processing.  
The scripts are designed to streamline the creation of patch-based datasets and the preparation of land cover reference layers used in Earth Observation and machine learning workflows.

## Contents

- **Patch extraction scripts** — define centers of image patches and build extent polygons around them.

- **CLC rasterization scripts** — convert **CORINE Land Cover (CLC)** or other vector-based land cover datasets into raster format, aligned with the corresponding Sentinel-2 grid and projection.

## Usage

1. Open QGIS and start the **Python Console** (`Plugins → Python Console`).  
2. Load and run the desired script. See instructions provided with each script.

## Notes

- The scripts are optimized for reproducibility and integration with the **SENSERO** dataset generation workflow.
