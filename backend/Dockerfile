# Backend image: the Django API with AMRFinderPlus for the gene model.
# Build from the project root (see .dockerignore for what is left out):
#   docker build -f backend/Dockerfile -t amr-backend .
# Run (production settings; see README §9 for the variables):
#   docker run -p 8000:8000 -e SECRET_KEY=... -e ALLOWED_HOSTS=localhost -e ADMIN_TOKEN=... amr-backend
FROM condaforge/miniforge3:24.7.1-0

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# AMRFinderPlus from bioconda, with its database, for the gene model (B6).
# Only needed if /predict serves a model with `needs_amrfinder`; the k-mer
# model does not use it (Hamza's choice, Week 3).
RUN conda install -n base -c conda-forge -c bioconda -y \
    ncbi-amrfinderplus=4.2.7 && \
    amrfinder -u && \
    conda clean -afy

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
# The timeout leaves room for a slow genome prediction.
CMD ["sh", "-c", "gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
