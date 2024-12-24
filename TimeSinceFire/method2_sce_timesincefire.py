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

# Define a function to visualize the processed data
def visualize_burn_map(combined_image, start_date, end_date, southern_california, palette, map_center):
    max_days = calculate_days(start_date, end_date)
    vis_params = {
        'bands': 'days_since_last_burn',
        'min': 1,
        'max': max_days,
        'palette': palette
    }

    m = folium.Map(location=map_center, zoom_start=7)

    masked_combined_image = combined_image.updateMask(combined_image.select('days_since_last_burn').neq(0))
    folium_add_ee_layer(m, masked_combined_image, vis_params, "Days Since Last Burn")
    folium.LayerControl().add_to(m)

    output_html = "southern_california_burn_map.html"
    m.save(output_html)

    print(f"Map saved to {output_html}. Open this file in your browser to view the map.")


########### Define values according to your requirements ###########
initialize_ee("test-09112024") #google earth engine project id
start_date = "2000-01-01"
end_date = "2024-09-30"
southern_california = ee.Geometry.BBox(-120.708008, 33.156797, -113.975687, 38.395343)
palette = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
map_center = [35.5688, -118.8678]

########### End of variable definitions ###########


# Process the data and generate visualizations
combined_image = process_modis_data(start_date, end_date, southern_california)
visualize_burn_map(combined_image, start_date, end_date, southern_california, palette, map_center)
