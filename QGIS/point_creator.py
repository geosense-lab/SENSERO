"""
QGIS AUTOMATION SCRIPT: Point–Square Synchronization with Raster Tagging
-----------------------------------------------------------------------

DESCRIPTION
This script automates the workflow of creating and maintaining fixed-size
squares (e.g. 3360 m × 3360 m) around points in a QGIS project.

Each time a point is added, moved, or deleted in the specified "points" layer:
  • a square polygon is automatically created, repositioned, or removed
    in a companion memory layer named "Squares_3360m";
  • the point’s attribute table is updated with the name of the topmost
    local raster layer that has valid data under the point ("top_raster").

The script also:
  • ensures the 'top_raster' field exists (adds it if missing);
  • keeps the squares layer editable for manual adjustments;
  • runs entirely within the current QGIS session (no plugins required).

USAGE
1. Load your raster(s) and point layer (default: layer named “points”). 
   Create the point layer if it doesn't exist.
2. Open the QGIS Python Console and paste the entire script.
3. Run it once per project/session.
4. Start editing the “points” layer:
      – When you add a point → a 3360 m square appears automatically,
        and the “top_raster” attribute is filled in.
      – When you move a point → the corresponding square moves too.
      – When you delete a point → its square is deleted.
5. The “Squares_3360m” layer remains editable and can be saved manually
   if you want to persist it.
6. Save the points layer when you finish adding points.   

NOTES
• The default coordinate reference system for square construction is
  EPSG:3844 (Stereo 70 – Romania). If your point layer is already in
  a projected CRS (meters), that CRS is used instead.
• Only local GDAL rasters (e.g., GeoTIFFs, VRTs) are queried to find
  the “underlying raster”; XYZ/WMS/WMTS layers are skipped to avoid delays.
• The form suppression and field configuration persist inside the project
  file (.qgz / .qgs), so you only need to run this script once per project.

Version: 1.0
Tested on: QGIS 3.40 "Bratislava" (and compatible LTR builds)
-----------------------------------------------------------------------
"""

# === QGIS Auto-patch: points ↔ 3360 m squares + raster tagging + move sync ===
from qgis.PyQt.QtCore import QSettings, QVariant
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeatureRequest,
    QgsWkbTypes, QgsMapLayer, QgsRaster, QgsFieldConstraints, QgsDefaultValue
)
import os

# ---------- SETTINGS ----------
POINT_LAYER_NAME   = "points"           # your editable point layer
OUT_LAYER_NAME     = "Squares_3360m"
SIDE_M             = 3360
DST_CRS_FALLBACK   = QgsCoordinateReferenceSystem("EPSG:3844")  # Stereo 70 (RO)
POINT_RASTER_FIELD = "top_raster"

# ---------- Suppress attribute form pop-up (project-wide + per-layer) ----------
for key in (
    'qgis/digitizing/disable_enter_attribute_values_dialog',
    'digitizing/disable_enter_attribute_values_dialog',
    'Qgis/digitizing/disable_enter_attribute_values_dialog'
):
    QSettings().setValue(key, True)

# ---------- Helpers ----------
def get_layer_by_name(name):
    lst = QgsProject.instance().mapLayersByName(name)
    return lst[0] if lst else None

def ensure_point_field(layer, name, qvariant_type=QVariant.String):
    if name not in [f.name() for f in layer.fields()]:
        layer.startEditing()
        layer.addAttribute(QgsField(name, qvariant_type))
        layer.commitChanges()

def ensure_out_layer(crs):
    lyr = get_layer_by_name(OUT_LAYER_NAME)
    if lyr is None:
        lyr = QgsVectorLayer(f"Polygon?crs={crs.authid()}", OUT_LAYER_NAME, "memory")
        lyr.dataProvider().addAttributes([
            QgsField("src_fid", QVariant.LongLong),
            QgsField("side_m",  QVariant.Int),
        ])
        lyr.updateFields()
        QgsProject.instance().addMapLayer(lyr)
    if not lyr.isEditable():
        lyr.startEditing()
    return lyr

def extract_point_xy(geom):
    if not geom or geom.isEmpty() or geom.type() != QgsWkbTypes.PointGeometry:
        return None
    if geom.isMultipart():
        pts = geom.asMultiPoint()
        return QgsPointXY(pts[0]) if pts else None
    return QgsPointXY(geom.asPoint())

def build_square(center_xy, side_m):
    h = side_m / 2.0
    x, y = center_xy.x(), center_xy.y()
    ring = [QgsPointXY(x-h,y-h), QgsPointXY(x+h,y-h), QgsPointXY(x+h,y+h),
            QgsPointXY(x-h,y+h), QgsPointXY(x-h,y-h)]
    return QgsGeometry.fromPolygonXY([ring])

def _is_local_file_raster(rlayer) -> bool:
    try:
        if rlayer.providerType().lower() != "gdal":
            return False  # skip XYZ/WMS/WMTS etc.
        src = rlayer.source().split("|", 1)[0].strip('"').strip("'")
        return os.path.exists(src)
    except Exception:
        return False

def get_underlying_raster_name_at_point(map_point_xy, src_crs) -> str:
    """Topmost local GDAL raster with non-nodata pixel at the point."""
    root = QgsProject.instance().layerTreeRoot()
    for lyr in reversed(root.layerOrder()):  # topmost first
        if lyr.type() != QgsMapLayer.RasterLayer:
            continue
        r = lyr
        if not _is_local_file_raster(r):
            continue
        try:
            ct = QgsCoordinateTransform(src_crs, r.crs(), QgsProject.instance())
            p = ct.transform(QgsPointXY(map_point_xy))
        except Exception:
            continue
        if not r.extent().contains(p):
            continue
        try:
            ident = r.dataProvider().identify(p, QgsRaster.IdentifyFormatValue)
            if not ident.isValid():
                continue
            vals = ident.results()
            for band, val in vals.items():
                if val is None:
                    continue
                try:
                    has_nd = r.dataProvider().sourceHasNoDataValue(band)
                    nd_val = r.dataProvider().sourceNoDataValue(band) if has_nd else None
                    if has_nd and val == nd_val:
                        continue
                except Exception:
                    pass
                return r.name()
        except Exception:
            continue
    return ""

# ---------- Get point layer & configure ----------
pt_layer = get_layer_by_name(POINT_LAYER_NAME)
if pt_layer is None:
    raise RuntimeError(f"Layer '{POINT_LAYER_NAME}' not found.")

# Remove old 'src_file' if present
src_idx = pt_layer.fields().indexOf('src_file')
if src_idx != -1:
    pt_layer.startEditing(); pt_layer.deleteAttribute(src_idx); pt_layer.commitChanges()

# Ensure top_raster field and defaults
ensure_point_field(pt_layer, POINT_RASTER_FIELD, QVariant.String)
idx = pt_layer.fields().indexOf(POINT_RASTER_FIELD)
if idx != -1:
    pt_layer.setFieldConstraint(idx,
        QgsFieldConstraints.ConstraintNotNull,
        QgsFieldConstraints.ConstraintStrengthNotSet
    )
    pt_layer.setDefaultValueDefinition(idx, QgsDefaultValue("''"))

# Suppress attribute form on add (persistent project property)
pt_layer.setCustomProperty("featformsuppress", 1)   # 1 = hide on add

# ---------- Output layer & transforms ----------
dst_crs = pt_layer.crs() if not pt_layer.crs().isGeographic() else DST_CRS_FALLBACK
out_layer = ensure_out_layer(dst_crs)
to_dst = QgsCoordinateTransform(pt_layer.crs(), dst_crs, QgsProject.instance())

# ---------- Handlers ----------
def _add_square_for_point(fid, pt_xy):
    pt_m = to_dst.transform(pt_xy)
    square = build_square(pt_m, SIDE_M)
    feat = QgsFeature(out_layer.fields())
    feat.setGeometry(square)
    feat["src_fid"] = int(fid)
    feat["side_m"]  = int(SIDE_M)
    out_layer.addFeature(feat)
    out_layer.updateExtents()

def _delete_squares_for_point_ids(fid_list):
    if not fid_list: return
    expr = f'"src_fid" IN ({",".join(map(str, fid_list))})'
    ids = [g.id() for g in out_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))]
    if ids:
        out_layer.deleteFeatures(ids)

def on_feature_added(fid):
    f = pt_layer.getFeature(fid)
    if not f: return
    pt = extract_point_xy(f.geometry())
    if pt is None: return
    try:
        name = get_underlying_raster_name_at_point(pt, pt_layer.crs())
        if name:
            i = pt_layer.fields().indexOf(POINT_RASTER_FIELD)
            if i >= 0:
                pt_layer.beginEditCommand("auto-tag raster")
                pt_layer.changeAttributeValue(fid, i, name)
                pt_layer.endEditCommand()
    except Exception:
        pass
    _add_square_for_point(fid, pt)

def on_feature_deleted(fid):
    _delete_squares_for_point_ids([fid])

def on_features_deleted(fids):
    _delete_squares_for_point_ids(list(fids))

# ---------- MOVE-SYNC: when a point moves, update its square ----------
def _update_square_for_point(fid, new_pt_map_crs):
    pt_m = to_dst.transform(new_pt_map_crs)
    new_square = build_square(pt_m, SIDE_M)
    expr = f'"src_fid" = {int(fid)}'
    ids = [g.id() for g in out_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))]
    if not ids:
        _add_square_for_point(fid, new_pt_map_crs)
        return
    if not out_layer.isEditable():
        out_layer.startEditing()
    out_layer.beginEditCommand("move-square")
    for gid in ids:
        out_layer.changeGeometry(gid, new_square)
    out_layer.endEditCommand()
    out_layer.updateExtents()

def on_point_geometry_changed(fid, new_geom):
    pt_xy = extract_point_xy(new_geom)
    if pt_xy is None:
        return
    _update_square_for_point(fid, pt_xy)

# ---------- Connect signals (avoid duplicates) ----------
for sig, func in (
    (getattr(pt_layer,'featureAdded',None), on_feature_added),
    (getattr(pt_layer,'featureDeleted',None), on_feature_deleted),
    (getattr(pt_layer,'featuresDeleted',None), on_features_deleted),
    (getattr(pt_layer,'geometryChanged',None), on_point_geometry_changed),
):
    if sig:
        try: sig.disconnect(func)
        except Exception: pass
        sig.connect(func)

print(f"✅ Ready: {POINT_LAYER_NAME}")
print("• Attribute form suppressed (Hide on Add)")
print("• top_raster auto-tagged with underlying raster name")
print(f"• Draws and syncs {SIDE_M} m squares in '{OUT_LAYER_NAME}' (CRS {dst_crs.authid()})")
print("• Squares are auto-removed on delete and moved when points move.")

