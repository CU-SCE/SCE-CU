# Project Overview

This repository contains two models designed for assessment of fuel conditions in Southern California. The models are organized into two folders: one for calculating the days since the last fire and another for performing MESMA (Multiple Endmember Spectral Mixture Analysis). 

## Folder 1: **Days Since Last Fire Calculation**

This model calculates the number of days since the most recent fire. The core functionality of this model is based on MODIS imagery data. The process involves:


## Folder 2: **MESMA (Multiple Endmember Spectral Mixture Analysis)**

This model downloads Sentinel satellite data for Southern California, preprocesses the images, and performs MESMA. MESMA is a spectral unmixing algorithm that decomposes a mixed pixel into a combination of endmembers and their fractional abundances. This process enables the calculation of the proportion of non-photosynthetically active vegetation (NPV) per pixel.

---

## Setup Instructions

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo-name.git
    ```

2. Navigate to the project directory:
    ```bash
    cd your-repo-name
    ```

3. Set up a virtual environment and install the dependencies:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    pip install -r requirements.txt
    ```

---

## How to Use

### **Days Since Last Fire Model**

1. Open the Jupyter Notebook in the `fire-analysis` folder.
2. Update the required variables (e.g., Google Earth Engine project ID, start and end dates).
3. Run the notebook to calculate the days since the last fire and generate an interactive map.

### **MESMA Model**

1. Open the Jupyter Notebook in the `mesma-analysis` folder.
2. Set the appropriate environmental variables and parameters.
3. Run the notebook to perform MESMA and analyze environmental similarity across Southern California.

---

For any issues or suggestions, feel free to open an issue in this repository.



