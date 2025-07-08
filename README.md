# Paperscope Simulation

Execute custom simulations via a headless QGIS in a docker container and PaperScope scenes as input data.

The following simulation algorithms are currently implemented:

• [umep:heat_island](https://umep-docs.readthedocs.io/en/latest/processor/Urban%20Heat%20Island%20TARGET.html)

## Development Setup

To set up the development environment, the **preferred method** is to use a development container. Alternatively, you can use a virtual environment.

### Preferred: Using a Development Container

For development, use a development container. Simply open this folder via VS-Code DevContainer and start the program from inside the container. The first parameter is a simulation id from the PaperScope WebInterface
```bash
python3 -m paperscope_simulation 39313074-e06d-45a6-9fac-2bb41a32feb3
```

If you have a local PaperScope WebInterface on your machine you can overwrite the default url with your local docker host url:
```bash
python3 -m paperscope_simulation 39313074-e06d-45a6-9fac-2bb41a32feb3 http://host.docker.internal/hcu/paperscope-website/public/
```


### Alternative: Using a Virtual Environment

1. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
   When using a virtual environment, ensure that:
   - QGIS and the plugins `umep` and `umep-processing` are installed.
   - The virtual environment uses the Python binary provided by QGIS.

2. **Install Dependencies**:
   Use the `pip install -e .[dev]` command to install the project in editable mode along with development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Running the Project

First build a Docker image from the project that can be used to run the simulation runner in a containerized environment.

1. Navigate to the root directory of the project where the Dockerfile is located.
2. Build the Docker image using the following command:
    ```
    docker build -t paperscope-simulation:latest .
    ```


Execute the following command to run a simulation. You need to bind your local storage with the image storage. The first parameter is a simulation id from the PaperScope WebInterface
```bash
docker run -v /my-local-storage/simulations:/app/storage paperscope-simulation:latest python3 -m paperscope_simulation 39313074-e06d-45a6-9fac-2bb41a32feb3
```

## PaperScope WebInterface

All simulations are managed by the PaperScope WebInterface, which implements an OGC API endpoint to interact with simulations (processes) and jobs. Because simulations are long-running tasks, it is important to have a queue with a high timeout (minimum 1 hour). Ensure that the queue in the WebInterface is started as follows:
```
php artisan queue:listen --timeout=3600
```