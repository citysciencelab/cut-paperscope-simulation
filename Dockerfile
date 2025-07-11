FROM qgis/qgis

# environment variables
ENV QT_QPA_PLATFORM=offscreen \
    XDG_RUNTIME_DIR=/tmp/runtime-root \
    DEBIAN_FRONTEND=noninteractive \
    LD_LIBRARY_PATH=/usr/lib/grass83/lib:/usr/lib \
    PYTHONPATH=/usr/share/qgis/python/plugins

# runtime directory
RUN mkdir -p /tmp/runtime-root && \
    chmod 700 /tmp/runtime-root && \
    echo "/usr/lib/grass83/lib" >> /etc/ld.so.conf.d/grass.conf && \
    ldconfig

# install system dependencies and QGIS
RUN --mount=type=cache,target=/var/cache/apt --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        unzip \
        qgis \
        qgis-plugin-grass \
        qgis-providers-common \
        qgis-providers && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install UMEP Processing
WORKDIR /usr/share/qgis/python/plugins
ADD https://github.com/UMEP-dev/UMEP-processing/archive/refs/heads/main.zip main.zip
RUN unzip main.zip && \
    rm main.zip && \
    mv UMEP-processing-main processing_umep && \
    ln -s /usr/share/qgis/python/plugins/UMEP-processing-main/ /usr/share/qgis/python/plugins/processing_umep

# install DGM1 Geländemodel
RUN mkdir -p /usr/share/gis-data
WORKDIR /usr/share/gis-data
ADD https://daten-hamburg.de/geographie_geologie_geobasisdaten/Digitales_Hoehenmodell/DGM1/dgm1_hh_2022-04-30.zip dgm1_hh_2022.zip
RUN unzip dgm1_hh_2022.zip && rm dgm1_hh_2022.zip

# install LGV Bodenbedeckung
WORKDIR /usr/share/gis-data
ADD https://paperscope.comodeling.city/storage/downloads/bodenbedeckung.zip bodenbedeckung.zip
RUN unzip bodenbedeckung.zip && rm bodenbedeckung.zip

# install LOD2 Buildings
WORKDIR /usr/share/gis-data
ADD https://paperscope.comodeling.city/storage/downloads/hh_lod2_buildings.zip buildings.zip
RUN unzip buildings.zip && rm buildings.zip

# virtual env with access to system packages
RUN python3 -m venv --system-site-packages /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# copy project files
WORKDIR /app
COPY . /app
COPY ./data/dgm1_hh_2022.vrt /usr/share/gis-data/dgm1_hh_2022-04-30/dgm1_hh_2022/dgm1_hh_2022.vrt

# install project dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --ignore-installed -e .
