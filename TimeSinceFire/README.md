# Time Since Fire

You will need python, jupyter notebook to run this. 
Unfortunately, running this code just through a plain python script will not give us the capabilities of rendering the map. Hence we must use jupyter notebooks.

## Steps to run this code

This code needs you to have an account with Google Earth Engine. It will avoid the hassles of downloading the images on local and processing it.

### Setup the virtual env
```sh
cd TimeSinceFire
python3 -m venv env #create a python virtual environment
source env/bin/activate
pip3 install -r requirements.txt
```

### Run the python notebook
```sh
jupyter notebook
```
In the last cell of the jupyter notebook make the necessary changes i.e
```
initialize_ee - add the google earth engine project id
start_date - start date of our fire analysis
end_date - end date of our fire analysis
southern_california - specify the bounds of southern_california or any rectangle bounding box for that matter
center - just focuses the map on this coordinate
palette - choose your colors for showing on the map
```

Now just run all the cells. When you click on the colors, you will be able to see the date of fire (in epoch format) and the number of days before the end_date the fire occured.