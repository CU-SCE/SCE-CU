FROM jupyter/base-notebook

USER root

# Set up package manager
RUN apt-get install -y apt-transport-https && \
    apt-get clean && apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository multiverse && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install some base software
RUN apt-get update --yes && \
    apt-get install --yes \
    fonts-dejavu \
    unixodbc \
    unixodbc-dev \
    curl \
    r-base \
    r-cran-rodbc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add sudo to jovyan user
RUN apt update && \
    apt install -y sudo && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*
    
# This is where we can control which root permissions the jovyan user will have
ARG PRIV_CMDS='/bin/ch*,/bin/cat,/bin/gunzip,/bin/tar,/bin/mkdir,/bin/ps,/bin/mv,/bin/cp,/usr/bin/apt*,/usr/bin/pip*,/bin/yum,/opt,/opt/conda/bin/*,/usr/bin/*'

RUN usermod -aG sudo jovyan && \
    echo "$LOCAL_USER ALL=NOPASSWD: $PRIV_CMDS" >> /etc/sudoers
RUN addgroup jovyan
RUN usermod -aG jovyan jovyan
    

# Install Geospatial libraries
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

# Update permissions for /opt/conda
RUN chown -R jovyan:users /opt/conda/share /usr/local/share /usr/local/bin/start-notebook.d 

USER jovyan

# Install jupyterlab and rstudio dependencies
RUN conda install -c conda-forge \ 
    jupyter_client \ 
    jupyter_core \ 
    jupyterlab_server \ 
    jupyter_server \
    r-rgl \
    r-htmlwidgets \
    r-htmltools && \ 
    jupyter lab clean

# Install and configure jupyter lab 
COPY jupyter_notebook_config.json /opt/conda/etc/jupyter/jupyter_notebook_config.json

# Rebuild the Jupyter Lab with new tools
RUN jupyter lab build

USER root

# Get the latest version from GitHub and set it as an environment variable
RUN CURRENT_VERSION=$(curl -Ls https://api.github.com/repos/Versent/saml2aws/releases/latest | grep 'tag_name' | cut -d'v' -f2 | cut -d'"' -f1) && \
    wget https://github.com/Versent/saml2aws/releases/download/v${CURRENT_VERSION}/saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz && \
	tar -xzvf saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz

# Extract the downloaded tarball
#RUN tar -xzvf saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz

# Move the binary to the local bin directory
RUN mv saml2aws /usr/local/bin/ && \
    chmod u+x /usr/local/bin/saml2aws

# Verify the installation
RUN saml2aws --version

USER jovyan

# Build Conda environment. Any packages you would like to install with conda need to be added to the environment.yml file in this Dockerfiles directory
RUN conda update -y conda && \
    conda config --remove channels conda-forge && \
    conda config --add channels conda-forge
WORKDIR /workspace
COPY environment.yml /workspace/ 
RUN mamba env create -f /workspace/environment.yml
RUN . /opt/conda/etc/profile.d/conda.sh && conda deactivate && conda activate preprocessing && python -m ipykernel install --name preprocessing

