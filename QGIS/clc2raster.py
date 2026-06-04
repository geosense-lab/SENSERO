"""
=============================================================
CLC Rasterization Script for QGIS - works with version 3.40 
=============================================================

🟢 BEFORE YOU RUN THIS SCRIPT

You must have these layers loaded (in this order in the Layers panel):

  1. Top layer   → CLC vector layer (clipped or full)
  2. Layer below → Reference raster (Sentinel-2 RGB GeoTIFF)

⚙️ What this does:
  • Reprojects the CLC layer to match the raster CRS.
  • Rasterizes it using the same extent, width, and height.
  • Automatically removes "_RGB432", "_RGB843", "_B432", "_B843"
    or any other trailing "_suffix" before saving outputs.
  • Produces:
        - Grayscale CLC.tif (UInt16, LZW+Predictor=2)
        - RGB colorized preview CLC_RGB.tif
=============================================================
"""

import os
import re
import numpy as np
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProcessingFeedback,
    QgsProcessingContext,
    QgsApplication,
)
import processing
from osgeo import gdal

# ----------------------------------------------------------
# 1) Identify top CLC vector and raster immediately below
# ----------------------------------------------------------
root = QgsProject.instance().layerTreeRoot()
layer_order = root.layerOrder()

if len(layer_order) < 2:
    raise RuntimeError("Please ensure at least two layers are loaded (top=CLC, below=raster).")

vector_layer = layer_order[0]    # top layer = CLC
raster_layer = layer_order[1]    # below = raster

if not isinstance(vector_layer, QgsVectorLayer):
    raise RuntimeError("Top layer must be a vector (CLC).")
if not isinstance(raster_layer, QgsRasterLayer):
    raise RuntimeError("The layer below must be a raster (GeoTIFF).")

label_field = "Code_18"

# ----------------------------------------------------------
# 2) Verify raster source and prepare clean output names
# ----------------------------------------------------------
raster_path = raster_layer.source()
if raster_path.startswith("type=xyz"):
    raise RuntimeError("The raster layer appears to be an XYZ basemap. Use a GeoTIFF instead.")
if not os.path.isfile(raster_path):
    raise RuntimeError(f"Raster file not found or not on disk: {raster_path}")

# ---- Clean output name (remove trailing _RGBxxx / _Bxxx / etc.) ----
base_full, _ = os.path.splitext(raster_path)
dir_name, base_name = os.path.split(base_full)

# Remove any of these endings: _RGB432, _RGB843, _B432, _B843, etc.
base_name_stripped = re.sub(r'_(RGB\d{3}|B\d{3}|[A-Za-z0-9]+)$', '', base_name)

out_base = os.path.join(dir_name, base_name_stripped)
out_gray = f"{out_base}_CLC.tif"
out_rgb  = f"{out_base}_CLC_RGB.tif"

width  = raster_layer.width()
height = raster_layer.height()
extent = raster_layer.extent()
crs    = raster_layer.crs()

print(f"Raster reference: {raster_path}")
print(f"Vector (CLC): {vector_layer.name()}")
print(f"Output grayscale: {out_gray}")
print(f"Output RGB: {out_rgb}")

# ----------------------------------------------------------
# 3) Reproject CLC vector to raster CRS
# ----------------------------------------------------------
fb = QgsProcessingFeedback()
context = QgsProcessingContext()

reproj = processing.run(
    "native:reprojectlayer",
    {"INPUT": vector_layer, "TARGET_CRS": crs, "OUTPUT": "memory:"},
    feedback=fb, context=context
)["OUTPUT"]

# ----------------------------------------------------------
# 4) Ensure label field exists and convert to integer
# ----------------------------------------------------------
if label_field not in [f.name() for f in reproj.fields()]:
    raise RuntimeError(f"Field '{label_field}' not found in {vector_layer.name()}.")

calc = processing.run(
    "native:fieldcalculator",
    {
        "INPUT": reproj,
        "FIELD_NAME": "clc_val",
        "FIELD_TYPE": 1,
        "FIELD_LENGTH": 10,
        "FIELD_PRECISION": 0,
        "NEW_FIELD": True,
        "FORMULA": f'to_int(\"{label_field}\")',
        "OUTPUT": "memory:",
    },
    feedback=fb, context=context
)["OUTPUT"]

# ----------------------------------------------------------
# 5) Rasterize (QGIS 3.40 compatible)
# ----------------------------------------------------------
alg = QgsApplication.processingRegistry().algorithmById("gdal:rasterize")

params = {
    "INPUT": calc,
    "FIELD": "clc_val",
    "WIDTH": width,
    "HEIGHT": height,
    "EXTENT": extent,
    "NODATA": 0,
    "INIT": 0,
    "INVERT": False,
    "DATA_TYPE": 5,  # UInt16
    "OPTIONS": "COMPRESS=LZW|PREDICTOR=2",
    "OUTPUT": out_gray,
}

result_tuple = alg.run(params, context, fb)
if isinstance(result_tuple, tuple):
    result, ok = result_tuple
else:
    result, ok = result_tuple, True

if not ok:
    raise RuntimeError("Rasterization failed (algorithm returned False).")

out_gray = result.get("OUTPUT", out_gray)
if not os.path.exists(out_gray):
    raise RuntimeError(f"Rasterization failed; file not found: {out_gray}")

print("✓ Grayscale CLC raster saved:", out_gray)

# ----------------------------------------------------------
# 6) Build RGB preview from grayscale
# ----------------------------------------------------------
style_map = {
 '111': (230, 0, 77), '112': (255, 0, 0), '121': (204, 77, 242), '122': (204, 0, 0),
 '123': (230, 204, 204), '124': (230, 204, 230), '131': (166, 0, 204), '132': (166, 77, 0),
 '133': (255, 77, 255), '141': (255, 166, 255), '142': (255, 230, 255), '211': (255, 255, 168),
 '212': (255, 255, 0), '213': (230, 230, 0), '221': (230, 128, 0), '222': (242, 166, 77),
 '223': (230, 166, 0), '231': (230, 230, 77), '241': (255, 230, 166), '242': (255, 230, 77),
 '243': (230, 204, 77), '244': (242, 204, 166), '311': (128, 255, 0), '312': (0, 166, 0),
 '313': (77, 255, 0), '321': (204, 242, 77), '322': (166, 255, 128), '323': (166, 230, 77),
 '324': (166, 242, 0), '331': (230, 230, 230), '332': (204, 204, 204), '333': (204, 255, 204),
 '334': (0, 0, 0), '335': (166, 230, 204), '411': (166, 166, 255), '412': (77, 77, 255),
 '421': (204, 204, 255), '422': (230, 230, 255), '423': (166, 166, 230), '511': (0, 204, 242),
 '512': (128, 242, 230), '521': (0, 255, 166), '522': (166, 255, 230), '523': (230, 242, 255)
}

ds = gdal.Open(out_gray, gdal.GA_ReadOnly)
band = ds.GetRasterBand(1)
arr = band.ReadAsArray()
gt = ds.GetGeoTransform()
prj = ds.GetProjection()
h, w = arr.shape

R = np.zeros((h, w), dtype=np.uint8)
G = np.zeros((h, w), dtype=np.uint8)
B = np.zeros((h, w), dtype=np.uint8)

for code_str, (r, g, b) in style_map.items():
    code_val = int(code_str)
    mask = (arr == code_val)
    if mask.any():
        R[mask] = r
        G[mask] = g
        B[mask] = b

drv = gdal.GetDriverByName("GTiff")
rgb_ds = drv.Create(out_rgb, w, h, 3, gdal.GDT_Byte,
                    options=["COMPRESS=LZW", "PREDICTOR=2"])
rgb_ds.SetGeoTransform(gt)
rgb_ds.SetProjection(prj)
rgb_ds.GetRasterBand(1).WriteArray(R)
rgb_ds.GetRasterBand(2).WriteArray(G)
rgb_ds.GetRasterBand(3).WriteArray(B)
rgb_ds.FlushCache()
rgb_ds = None
ds = None

print("✓ RGB CLC preview saved:", out_rgb)

# ----------------------------------------------------------
# 7) Add outputs back to QGIS
# ----------------------------------------------------------
QgsProject.instance().addMapLayer(QgsRasterLayer(out_gray, os.path.basename(out_gray)))
QgsProject.instance().addMapLayer(QgsRasterLayer(out_rgb, os.path.basename(out_rgb)))
print("🎯 Done. Both CLC rasters added to QGIS.")
