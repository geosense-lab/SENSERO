# Patch Center Coordinates

This folder contains all **Parquet files** that store the **geographic coordinates (longitude and latitude)** of the **center points** of image patches extracted from Sentinel-2 scenes.

Each record includes:
- **FILENAME** – the original Sentinel-2 scene identifier  
- **LONGITUDE** – geographic longitude of the patch center (WGS84)  
- **LATITUDE** – geographic latitude of the patch center (WGS84)  

These coordinates define the central position of every extracted patch and can be used to locate them spatially or to reconstruct the patch layout for mapping or validation tasks.

**Example:**

| FILENAME  | LONGITUDE  | LATITUDE |
|-----------|------------|-----------|
| S2A_MSIL2A_20180928T090731_N0500_R050_T35TMN | 26.058908 | 47.808726 |
| S2A_MSIL2A_20180928T090731_N0500_R050_T35TMN | 26.193757 | 47.820729 |
| S2A_MSIL2A_20180928T090731_N0500_R050_T35TMN | 26.314743 | 47.827378 |

---

In addition, a **Shapefile (`.shp`)** is provided for convenient visualization and spatial analysis in **QGIS** or other GIS software.  
The shapefile contains the same fields as the Parquet files and can be loaded directly into QGIS.

---

**Usage:**
- Open the `.shp` file in **QGIS** to visualize patch centers.
- Load the Parquet files into **Python (pandas/geopandas)** for further analysis or automated processing.
