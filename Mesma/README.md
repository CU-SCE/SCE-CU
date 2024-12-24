# MESMA
Author: Daksha Singhal

---

## Requirements

Ensure the following software and dependencies are installed:

- **Python**: Version 3.10
- **Conda**: Anaconda or Miniconda for environment management
- **Pip**: Python package manager
- **Git**: Version control system
- **Optional**: Docker for containerized execution

---

## Running the Code

### Running the Jupyter Notebooks

#### **1. Running "download_sentinel_images.ipynb"**

1. Update the **AWS bucket name** and **prefix** in the **second cell**.
2. Specify the **start date** and **end date** for downloading the Sentinel-2 images.
3. The images will be downloaded and stored in the specified AWS bucket.

#### **2. Running "Image_Preprocessing.ipynb"**

1. Update the temporary AWS credentials in the **fourth cell**.
2. Set the **AWS bucket input folder** to the prefix from the previous script (this is the folder containing the downloaded Sentinel images).
3. Define the **AWS bucket folder** for storing the preprocessed images.

#### **3. "Running mesma_main.py"**
Execute the script as per your environment setup and requirements. 

 ```bash
   python mesma_main.py spectral_library/38_output.sli Type "11_S_NT_2024_9_11.tif"
   ```


---


