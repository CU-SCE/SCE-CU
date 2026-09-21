"""Method 2 — Southern California days-since-last-burn map.

Same MODIS MCD64A1 logic as SCE-CU TimeSinceFire method 2, but the fire
layer is a **fixed PNG** (ImageOverlay). The old Folium version used
Earth Engine tile URLs that expire, so the colors vanished.

Run once on CyVerse after Earth Engine auth:
  python method2.py

Writes:
  southern_california_burn_map.html
  southern_california_burn_map.png
"""

from __future__ import annotations

import base64
import datetime
import urllib.request
from pathlib import Path

import ee
import folium
from folium.raster_layers import ImageOverlay


def initialize_ee(project_id):
    try:
        ee.Initialize(project=project_id)
        print(f"Earth Engine initialized (project={project_id})")
        return
    except Exception as e:
        print("Initialize failed, authenticating...", e)

    try:
        ee.Authenticate(auth_mode="notebook")
    except Exception:
        ee.Authenticate()

    ee.Initialize(project=project_id)
    print(f"Earth Engine initialized after auth (project={project_id})")


def compute_date_ranges(start_date, end_date):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    date_ranges = []
    current_year = start.year
    while current_year <= end.year:
        range_start = start_date if current_year == start.year else f"{current_year}-01-01"
        range_end = end_date if current_year == end.year else f"{current_year}-12-31"
        date_ranges.append([range_start, range_end])
        current_year += 1
    return date_ranges


def process_modis_data(start_date, end_date, southern_california):
    reference_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    reference_date_millis = int(reference_date.timestamp() * 1000)
    date_ranges = compute_date_ranges(start_date, end_date)

    def create_tiff_and_extract_data(range_start, range_end):
        modis_burned_area = (
            ee.ImageCollection("MODIS/061/MCD64A1")
            .filter(ee.Filter.date(range_start, range_end))
            .filterBounds(southern_california)
        )
        burned_area = modis_burned_area.select("BurnDate")
        latest_burn = burned_area.reduce(ee.Reducer.max()).rename("latest_burn_date")
        clipped_burn = latest_burn.clip(southern_california)

        def julian_to_date(image):
            burn_date = image.select("latest_burn_date")
            start_of_year_millis = ee.Date(range_start).millis()
            return burn_date.expression(
                "burn_date == 0 ? 0 : startOfYear + (burn_date - 1) * 86400000",
                {"burn_date": burn_date, "startOfYear": start_of_year_millis},
            ).rename("yearly_burn_date")

        return julian_to_date(clipped_burn).toFloat()

    most_recent_burn = ee.Image(0).rename("most_recent_burn_date").clip(southern_california).toFloat()
    for range_start, range_end in date_ranges:
        yearly_burn_date = create_tiff_and_extract_data(range_start, range_end)
        most_recent_burn = most_recent_burn.where(yearly_burn_date.gt(most_recent_burn), yearly_burn_date)

    days_since_burn = most_recent_burn.expression(
        "burn_date == 0 ? 0 : round((reference_date - burn_date) / (1000 * 60 * 60 * 24))",
        {"reference_date": reference_date_millis, "burn_date": most_recent_burn},
    ).rename("days_since_last_burn").toFloat()

    return most_recent_burn.addBands(days_since_burn)


LEGEND_ITEMS = [
    ("#ffff00", "1 – 365 days (0 – 1 year)"),
    ("#ffd000", "366 – 730 days (1 – 2 years)"),
    ("#ff9f00", "731 – 1,825 days (2 – 5 years)"),
    ("#ff6b00", "1,826 – 3,650 days (5 – 10 years)"),
    ("#f03b20", "3,651 – 7,300 days (10 – 20 years)"),
    ("#b10026", "> 7,300 days (> 20 years)"),
    ("#808080", "0 days (No fire detected)"),
]


def classify_days_since_burn(combined_image):
    days = combined_image.select("days_since_last_burn")
    classified = (
        ee.Image(0)
        .where(days.gte(1).And(days.lte(365)), 1)
        .where(days.gte(366).And(days.lte(730)), 2)
        .where(days.gte(731).And(days.lte(1825)), 3)
        .where(days.gte(1826).And(days.lte(3650)), 4)
        .where(days.gte(3651).And(days.lte(7300)), 5)
        .where(days.gt(7300), 6)
        .rename("burn_age_class")
        .toInt()
    )
    return classified


def add_burn_legend(map_object, reference_date):
    rows = "".join(
        f'<div style="margin:4px 0;display:flex;align-items:center;">'
        f'<span style="background:{color};width:16px;height:16px;'
        f'display:inline-block;margin-right:8px;border:1px solid #555;"></span>'
        f'<span>{label}</span></div>'
        for color, label in LEGEND_ITEMS
    )
    legend_html = f"""
    <div style="
        position: fixed;
        top: 12px;
        left: 12px;
        z-index: 9999;
        background: white;
        padding: 12px 14px;
        border: 2px solid #444;
        border-radius: 6px;
        font-size: 13px;
        font-family: Arial, sans-serif;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.25);
        max-width: 280px;
    ">
      <div style="font-weight:bold;margin-bottom:8px;">Days Since Last Burn</div>
      {rows}
      <hr style="margin:8px 0;">
      <div><b>Reference date:</b> {reference_date}</div>
      <div><b>Data source:</b> MODIS MCD64A1</div>
      <div style="margin-top:6px;color:#555;">Fixed PNG overlay (does not expire)</div>
    </div>
    """
    map_object.get_root().html.add_child(folium.Element(legend_html))


def find_out_dir() -> Path:
    for p in (
        Path("/home/jovyan/data-store/new_data/Time_since_fire"),
        Path("/data-store/iplant/home/samiksha23/SCE-CU/sentinel2_data/new_data/Time_since_fire"),
        Path("/home/jovyan/data-store/iplant/home/samiksha23/SCE-CU/sentinel2_data/new_data/Time_since_fire"),
        Path.cwd() / "new_data" / "Time_since_fire",
        Path.cwd(),
    ):
        if p.exists() or p.parent.exists():
            p.mkdir(parents=True, exist_ok=True)
            return p
    Path.cwd().mkdir(parents=True, exist_ok=True)
    return Path.cwd()


def download_classified_png(classified, region, png_path: Path, vis_params: dict) -> None:
    """Save the classified burn map once. This PNG is the layer the HTML uses."""
    url = classified.getThumbURL(
        {
            "min": vis_params["min"],
            "max": vis_params["max"],
            "palette": vis_params["palette"],
            "region": region,
            "dimensions": 2048,
            "format": "png",
        }
    )
    print("Downloading static burn PNG (this is the only Earth Engine fetch)...")
    urllib.request.urlretrieve(url, png_path)
    print(f"Wrote {png_path} ({png_path.stat().st_size / 1e6:.2f} MB)")


def visualize_burn_map(combined_image, start_date, end_date, southern_california, map_center, out_dir: Path):
    classified = classify_days_since_burn(combined_image)
    classified = classified.updateMask(classified.neq(0))
    vis_params = {
        "min": 1,
        "max": 6,
        "palette": [c for c, _ in LEGEND_ITEMS[:6]],
    }

    png_path = out_dir / "southern_california_burn_map.png"
    html_path = out_dir / "southern_california_burn_map.html"
    download_classified_png(classified, southern_california, png_path, vis_params)

    # Embed PNG so the HTML is self-contained (no expiring GEE tiles).
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    data_url = f"data:image/png;base64,{encoded}"
    bounds = [[32.50, -122.80], [37.10, -114.75]]  # south, west / north, east

    m = folium.Map(location=map_center, zoom_start=7, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Streets (with place names)",
        control=True,
        show=True,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Topo (with place names)",
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri",
        name="Satellite",
        control=True,
        show=False,
    ).add_to(m)

    ImageOverlay(
        image=data_url,
        bounds=bounds,
        opacity=0.75,
        name="Days Since Last Burn",
        overlay=True,
        control=True,
    ).add_to(m)
    folium.LayerControl().add_to(m)
    add_burn_legend(m, end_date)

    m.save(str(html_path))
    print(f"Map saved to {html_path}. Colors are a fixed PNG — no need to re-run Earth Engine to view.")


########### Define values according to your requirements ###########
initialize_ee("timesincefire")
start_date = "2000-01-01"
end_date = "2026-07-28"  # match the MESMA atlas date
southern_california = ee.Geometry.BBox(-122.80, 32.50, -114.75, 37.10)
map_center = [34.80, -118.775]
########### End of variable definitions ###########

out_dir = find_out_dir()
print("Output folder:", out_dir)
combined_image = process_modis_data(start_date, end_date, southern_california)
visualize_burn_map(combined_image, start_date, end_date, southern_california, map_center, out_dir)
