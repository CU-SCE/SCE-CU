FROM jupyter/base-notebook

USER root

# Set up the package manager
RUN apt-get install -y apt-transport-https && \
    apt-get clean && apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository multiverse && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the necessary base software
RUN apt-get update --yes && \
    apt-get install --yes \
    fonts-dejavu \
    unixodbc \
    unixodbc-dev \
    curl \
    r-base \
    r-cran-rodbc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Grant sudo privileges to the jovyan user
RUN apt update && \
    apt install -y sudo && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*
    
# Define the specific root permissions for the jovyan user here
ARG PRIV_CMDS='/bin/ch*,/bin/cat,/bin/gunzip,/bin/tar,/bin/mkdir,/bin/ps,/bin/mv,/bin/cp,/usr/bin/apt*,/usr/bin/pip*,/bin/yum,/opt,/opt/conda/bin/*,/usr/bin/*'

RUN usermod -aG sudo jovyan && \
    echo "$LOCAL_USER ALL=NOPASSWD: $PRIV_CMDS" >> /etc/sudoers
RUN addgroup jovyan
RUN usermod -aG jovyan jovyan
    

# Install the required geospatial libraries
RUN apt-get update && \
    apt install -y \
    gdal-bin \
    lbzip2 \
    libfftw3-dev \
    libgdal-dev \
    libgeos-dev \
    libgsl0-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libhdf4-alt-dev \
    libhdf5-dev \
    libjq-dev \
    libpq-dev \
    libproj-dev \
    libprotobuf-dev \
    libnetcdf-dev \
    libsqlite3-dev \
    libudunits2-dev \
    lsb-release \
    netcdf-bin \
    postgis \
    protobuf-compiler \
    sqlite3 \
    tk-dev \
    libfmt-dev \
    unixodbc-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# Update the permissions for the /opt/conda directory
RUN chown -R jovyan:users /opt/conda/share /usr/local/share /usr/local/bin/start-notebook.d 
RUN mkdir -p /home/jovyan/.cache/conda && chown -R jovyan:users /home/jovyan/.cache


USER jovyan
# Install dependencies for JupyterLab and RStudio
RUN conda install -c conda-forge \ 
    jupyter_client \ 
    jupyter_core \ 
    jupyterlab_server \ 
    jupyter_server \
    r-rgl \
    r-htmlwidgets \
    r-htmltools && \ 
    jupyter lab clean

# Install and configure JupyterLab
COPY internal_scripts/jupyter_notebook_config.json /opt/conda/etc/jupyter/jupyter_notebook_config.json

# Rebuild JupyterLab to include the new tools
RUN jupyter lab build

USER root

# Get the latest version from GitHub and set it as an environment variable
RUN CURRENT_VERSION=$(curl -Ls https://api.github.com/repos/Versent/saml2aws/releases/latest | grep 'tag_name' | cut -d'v' -f2 | cut -d'"' -f1) && \
    wget https://github.com/Versent/saml2aws/releases/download/v${CURRENT_VERSION}/saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz && \
	tar -xzvf saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz

# Extract the downloaded tarball file
#RUN tar -xzvf saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz

# Move the binary to the local bin directory
RUN mv saml2aws /usr/local/bin/ && \
    chmod u+x /usr/local/bin/saml2aws

# Verify the installation
RUN saml2aws --version

USER jovyan

# Build the Conda environment. Add any desired Conda packages to the environment.yml file located in the Dockerfiles directory
RUN conda update -y conda && \
    conda config --remove channels conda-forge && \
    conda config --add channels conda-forge
WORKDIR /workspace
COPY internal_scripts/environment.yml /workspace/ 
RUN mamba env create -f /workspace/environment.yml
COPY internal_scripts/run_mesma.py /workspace/
COPY internal_scripts/entrypoint.py /workspace/

COPY internal_scripts/core.py /home/user/anaconda3/envs/earth-lab/lib/python3.9/site-packages/mesma/hubdc/core.py
COPY internal_scripts/operators.py /home/user/anaconda3/envs/earth-lab/lib/python3.9/site-packages/mesma/interfaces/operators.py
COPY internal_scripts/writer.py /home/user/anaconda3/envs/earth-lab/lib/python3.9/site-packages/mesma/hubdc/writer.py



# RUN . /opt/conda/etc/profile.d/conda.sh && conda deactivate && conda activate earth-lab && python -m ipykernel install --name earth-lab
SHELL ["conda", "run", "-n", "earth-lab", "/bin/bash", "-c"]

# Run this env by default
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "earth-lab", "python", "entrypoint.py"]


# ENTRYPOINT ["python", "entrypoint.py"]

