# Backend image: the Django API with AMRFinderPlus for the gene model.
# Build from the project root (see .dockerignore for what is left out):
#   docker build -f backend/Dockerfile -t amr-backend .
# Run (production settings; see README §9 for the variables):
#   docker run -p 8000:8000 -e SECRET_KEY=... -e ALLOWED_HOSTS=localhost -e ADMIN_TOKEN=... amr-backend
FROM condaforge/miniforge3:24.7.1-0

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# AMRFinderPlus from bioconda for the gene model: /predict uses it when it is
# installed (backend/ml_models/genome_predictor.py), else the k-mer model.
RUN conda install -n base -c conda-forge -c bioconda -y \
    ncbi-amrfinderplus=4.2.7 && \
    conda clean -afy

# Its database pinned to the version the gene model was trained with, not the
# newest that `amrfinder -u` would fetch, so gene and mutation names match
# training. Put where AMRFinderPlus looks by default (data/latest) and named in
# AMRFINDER_DATABASE, which genome_predictor.py passes as --database. Change
# both together with a gene model retrained on a newer database.
ENV AMRFINDER_DB_VERSION=2026-08-07.1
ENV AMRFINDER_DATABASE=/opt/conda/share/amrfinderplus/data/${AMRFINDER_DB_VERSION}
COPY backend/docker/fetch_amrfinder_db.py /tmp/fetch_amrfinder_db.py
RUN python /tmp/fetch_amrfinder_db.py "$AMRFINDER_DB_VERSION" "$AMRFINDER_DATABASE" && \
    amrfinder_index "$AMRFINDER_DATABASE" && \
    ln -sfn "$AMRFINDER_DB_VERSION" "$(dirname "$AMRFINDER_DATABASE")/latest" && \
    amrfinder --database "$AMRFINDER_DATABASE" --database_version && \
    rm /tmp/fetch_amrfinder_db.py

# Python dependencies first, so code changes do not reinstall them.
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
# The K-mer model (kmer_resistance_model.pkl) was pickled with scikit-learn
# 1.6.1: the server loads it with that exact version, so no
# InconsistentVersionWarning and no risk of changed results. Update this pin
# only together with a re-saved model.
RUN python -m pip install --no-cache-dir scikit-learn==1.6.1

# The backend only: .dockerignore keeps Data/, experiments/ and the rest out.
COPY backend/ /app/backend/
WORKDIR /app/backend

EXPOSE 8000

# gunicorn, not runserver. Railway sets PORT; locally it defaults to 8000.
# The timeout leaves room for a slow genome prediction: a gene model runs
# AMRFinderPlus on the upload (10-45 s). It stays above the frontend's
# PREDICT_TIMEOUT (120 s, frontend/app.py), so the page gives up first and
# shows a message instead of the worker being killed mid-answer.
CMD ["sh", "-c", "gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 150"]
