# Time Since Fire

## Aim
Through this code we aim to analyse a region on earth between a certain timeframe for the most recent occurences of fires. For example consider these values - start_date is 2000-01-01 and end_date is 2024-11-30 and the region of interest is Southern California. We want to analyze and visualize all the areas of Southern California for fire events during those years. We want to compute the exact date on which a recent fire was observed and the number of days since end_date a fire was seen back in time.

You will need python and jupyter notebook to run this.   
*You will need to create an accout with Google Earth Engine, create a project and get the project id.*  
Unfortunately, running this code just through a plain python script will not give us the capabilities of rendering the map. Hence we suggest using jupyter notebooks.

## Steps to run this code

This code needs you to have an account with Google Earth Engine.    
It will avoid the hassles of downloading the images on local and processing it.  
Please setup the virtual env and install the dependencies, then run either of method 1 (preferred) or method 2.

### Setup the virtual env
```sh
cd TimeSinceFire
python3 -m venv fire #create a python virtual environment
source fire/bin/activate
pip3 install -r requirements.txt
```

### Method 1 (Preferred) - Run the python notebook
This method gives you an interactive map, that displays the latitude, longitude, date of fire in epoch format(most recent burn date) and the number of days before the end_date the fire occured (Days since Last Burn).
```sh
jupyter notebook
#<open method1_sce_timesincefire.ipynb>
```
It will ask you for authentication with your Google Account. Please complete that step.

In the last cell of the jupyter notebook make the necessary changes i.e
```
initialize_ee - add the google earth engine project id here
start_date - start date of our fire analysis
end_date - end date of our fire analysis
southern_california - specify the bounds of southern_california or any rectangle bounding box for that matter
center - just focuses the map on this coordinate
palette - choose your colors for showing on the map
```

### Method 2 - Run the python script
This code works similar to the the one present in the notebook, but this doesn't allow any interactions with the map. The output is stored as a southern_california_burn_map.html. You can just open this map on any browser by double clicking it.  
This is helpful to just grasp an idea of the spread in fire dates across that region and guage how recent or old the fire was. You can change the values of the variables(same as the ones above) in the last part of the code.
```sh
#assuming that you already have done the virtual env setup initially
python3 method2_sce_timesincefire.py
#this will generate southern_california_burn_map.html and you can open this file in a browser
```

## Sample outputs
![method1_sce_timesincefire](SampleOutputs/Method1.png)