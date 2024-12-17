# MESMA

---

## Requirements

Ensure you have the following software and dependencies installed:

- **Python**: Version 3.10
- **Conda**: Anaconda or Miniconda for environment management
- **Pip**: Python package manager
- **Git**: Version control
- **Optional**: Docker for containerized runs

---


## Running the Code

### Running the Jupyter Notebooks

#### **1. Running "download_sentinel_images.ipynb"**

1. Update the **AWS bucket name** and **prefix** in the **second cell**.
2. Specify the **start date** and **end date** for the Sentinel-2 images.
3. The images will be downloaded and stored in the specified bucket.

#### **2. Running "Image_Preprocessing.ipynb"**

1. Update the temporary AWS credentials in the **fourth cell**.
2. Update the **AWS bucket input folder** containing the downloaded Sentinel images (this will match the prefix from the previous script).
3. Set the **AWS bucket folder** for storing the preprocessed images.

#### **3. "Running mesma_main.py"**
 ```bash
   python mesma_main.py spectral_library/38_output.sli Type "11_S_NT_2024_9_11.tif"
   ```


---


