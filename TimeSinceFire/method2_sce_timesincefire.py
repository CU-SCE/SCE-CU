import ee
import folium
import datetime

# Define a function to add Earth Engine layers to Folium maps
def folium_add_ee_layer(map_object, ee_image_object, vis_params, name):
    tile_url = ee.Image(ee_image_object).getMapId(vis_params)['tile_fetcher'].url_format
    folium.TileLayer(
        tiles=tile_url,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True
    ).add_to(map_object)

# Authenticate and initialize the Google Earth Engine API
def initialize_ee(project_id):
    try:
        ee.Initialize(project=project_id)
    except ee.EEException:
        ee.Authenticate()
        ee.Initialize(project=project_id)

# Define a function to compute date ranges per year
def compute_date_ranges(start_date, end_date):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    # Generate a list of date ranges
    date_ranges = []
    current_year = start.year

    while current_year <= end.year:
        range_start = start_date if current_year == start.year else f"{current_year}-01-01"
        range_end = end_date if current_year == end.year else f"{current_year}-12-31"
        date_ranges.append([range_start, range_end])
        current_year += 1

    return date_ranges

# Define a function to calculate the number of days between two dates
def calculate_days(start_date, end_date):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    return (end - start).days

# Define a function to process MODIS data and return a combined image
def process_modis_data(start_date, end_date, southern_california):
    reference_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    reference_date_millis = int(reference_date.timestamp() * 1000)

    date_ranges = compute_date_ranges(start_date, end_date)

    def create_tiff_and_extract_data(range_start, range_end):
        modis_burned_area = ee.ImageCollection('MODIS/061/MCD64A1')\
            .filter(ee.Filter.date(range_start, range_end))\
            .filterBounds(southern_california)

        burned_area = modis_burned_area.select('BurnDate')
        latest_burn = burned_area.reduce(ee.Reducer.max()).rename('latest_burn_date')
        clipped_burn = latest_burn.clip(southern_california)

        def julian_to_date(image):
            burn_date = image.select('latest_burn_date')
            start_of_year_millis = ee.Date(range_start).millis()
            return burn_date.expression(
                'burn_date == 0 ? 0 : startOfYear + (burn_date - 1) * 86400000', {
                    'burn_date': burn_date,
                    'startOfYear': start_of_year_millis
                }).rename("yearly_burn_date")

        return julian_to_date(clipped_burn).toFloat()

    most_recent_burn = ee.Image(0).rename('most_recent_burn_date').clip(southern_california).toFloat()

    for range_start, range_end in date_ranges:
        yearly_burn_date = create_tiff_and_extract_data(range_start, range_end)
        most_recent_burn = most_recent_burn.where(
            yearly_burn_date.gt(most_recent_burn), yearly_burn_date
        )

    days_since_burn = most_recent_burn.expression(
        'burn_date == 0 ? 0 : round((reference_date - burn_date) / (1000 * 60 * 60 * 24))', {
            'reference_date': reference_date_millis,
            'burn_date': most_recent_burn
        }
    ).rename("days_since_last_burn").toFloat()

    return most_recent_burn.addBands(days_since_burn)

# Discrete age classes for clearer visualization (matches legend)
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
    """Map continuous days_since_last_burn into discrete classes 1–6."""
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
    """Add an HTML legend matching Days Since Last Burn classes."""
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
    </div>
    """
    map_object.get_root().html.add_child(folium.Element(legend_html))


# Define a function to visualize the processed data
def visualize_burn_map(combined_image, start_date, end_date, southern_california, palette, map_center):
    classified = classify_days_since_burn(combined_image)
    # Hide "no fire" (class 0); show classes 1–6
    classified = classified.updateMask(classified.neq(0))

    vis_params = {
        "min": 1,
        "max": 6,
        "palette": [c for c, _ in LEGEND_ITEMS[:6]],
    }

    m = folium.Map(location=map_center, zoom_start=7)
    folium_add_ee_layer(m, classified, vis_params, "Days Since Last Burn")
    folium.LayerControl().add_to(m)
    add_burn_legend(m, end_date)

    output_html = "southern_california_burn_map.html"
    m.save(output_html)

    print(f"Map saved to {output_html}. Open this file in your browser to view the map.")


########### Define values according to your requirements ###########
initialize_ee("timesincefire")  # must match GEE project id exactly (lowercase)
start_date = "2000-01-01"
end_date = "2024-09-30"
# Same AOI as Copernicus download / method1
southern_california = ee.Geometry.BBox(-122.80, 32.50, -114.75, 37.10)
palette = ['yellow', '#ffd000', '#ff9f00', '#ff6b00', '#f03b20', '#b10026']
map_center = [34.80, -118.775]

########### End of variable definitions ###########


# Process the data and generate visualizations
combined_image = process_modis_data(start_date, end_date, southern_california)
visualize_burn_map(combined_image, start_date, end_date, southern_california, palette, map_center)


!yes gocmd put southern_california_burn_map.html /iplant/home/samiksha23/SCE-CU/sentinel2_data/new_data/Time_since_fire
