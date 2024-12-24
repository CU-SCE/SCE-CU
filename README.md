
This repository contains two models designed for assessment of fuel conditions in Southern California. The models are organized into two folders: one for calculating the days since the last fire and another for performing Multiple Endmember Spectral Mixture Analysis (MESMA). 

## Folder 1: **Days Since Last Fire Calculation**

This model calculates the number of days since the most recent fire. The core functionality of this model is based on MODIS imagery data. 


## Folder 2: **MESMA**

This model downloads Sentinel satellite data for Southern California, preprocesses the images, and performs Multiple Endmember Spectral Mixture Analysis (MESMA). MESMA is a spectral unmixing algorithm that decomposes a mixed pixel into a combination of endmembers and their fractional abundances. This process enables the calculation of the proportion of non-photosynthetically active vegetation (NPV) per pixel.

---

## Setup Instructions

1. Clone the Repository:
   
    ```bash
    git clone https://github.com/your-repo-name.git
    ```

2. Navigate to the Project Directory:
   
    ```bash
    cd your-repo-name
    ```

3. Refer to Folder-Specific Instructions
Each folder contains its own Readme file with detailed instructions. Please follow them for additional setup or usage information.
    
---

For any issues or suggestions, feel free to open an issue in this repository.



