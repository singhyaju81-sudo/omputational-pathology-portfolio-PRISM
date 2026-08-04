"""Load a QuPath GeoJSON export, merge fragmented polygons by class.

QuPath exports in full-resolution pixel space == openslide level-0 coords,
so no conversion is needed. Always crop-and-verify a region before trusting it.
"""
import json
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from collections import defaultdict


def load_regions(geojson_path):
    d = json.load(open(geojson_path))
    feats = d["features"] if isinstance(d, dict) else d
    by_class = defaultdict(list)
    for f in feats:
        p = f.get("properties", {})
        c = p.get("classification", {})
        name = (c.get("name") if isinstance(c, dict) else None) or p.get("name") or "unclassified"
        by_class[name].append(shape(f["geometry"]).buffer(0))  # buffer(0) repairs self-intersections
    return {k: unary_union(v) for k, v in by_class.items()}


def tile_in_region(poly, x, y, tile=512):
    """True if the tile's centre falls inside the region polygon."""
    return poly.contains(Point(x + tile // 2, y + tile // 2))


if __name__ == "__main__":
    regions = load_regions("regions_all.geojson")
    for name, poly in regions.items():
        print(f"{name:16s} area={poly.area:,.0f} px^2")
