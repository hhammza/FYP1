FROM condaforge/miniforge3:24.7.1-0

WORKDIR /app

# Install AMRFinderPlus from bioconda and initialize its database.
RUN conda install -n base -c conda-forge -c bioconda -y \
    ncbi-amrfinderplus=4.2.7 && \
    amrfinder -u

# Install Python runtime dependencies for the Django backend.
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the project source.
COPY . /app
WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
