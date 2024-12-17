# MESMA

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Running the Code](#running-the-code)

---

## Requirements

Ensure you have the following software and dependencies installed:

- **Python**: Version 3.10
- **Conda**: Anaconda or Miniconda for environment management
- **Pip**: Python package manager
- **Git**: Version control
- **Optional**: Docker for containerized runs

---

## Installation

### Setting up the Anaconda Virtual Environment

1. **Create a separate anaconda virtual environment for each script**:
   ```bash
   conda create --name download_images python=3.10
   conda activate download_images
   ```

2. **Install additional dependencies for Jupyter Kernel**:
   ```bash
   conda install -c anaconda ipykernel
   python -m ipykernel install --user --name=download_images
   ```

3. **Clone the repository**:
   ```bash
   git clone https://github.com/viriglesias/SCE.git
   cd SCE
   ```


---

## Running the Code

### Running the Jupyter Notebooks

#### **1. Running "1. download_sentinel_images.ipynb"**

1. Install the libraries by running the **first cell**.
2. Update the **AWS bucket name** and **prefix** in the **second cell**.
3. Specify the **start date** and **end date** for the Sentinel-2 images.
4. The images will be downloaded and stored in the specified bucket.

#### **2. Running "2. Image_Preprocessing.ipynb"**

1. Install the libraries by running the **first cell**.
2. Update the temporary AWS credentials in the **fourth cell**.
3. Update the **AWS bucket input folder** containing the downloaded Sentinel images (this will match the prefix from the previous script).
4. Set the **AWS bucket folder** for storing the preprocessed images.


---


