FROM selenium/standalone-chrome:4.21.0-20240522

USER root
# Install packages for python
RUN --mount=type=cache,sharing=private,target=/var/cache/apt apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libffi-dev \
        libssl-dev \
        zlib1g-dev \
        liblzma-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libgl1-mesa-glx \
        libsm6 \
        libxext6 \
        xterm \
        python3 \
        python3-venv \
        pip \
        python3-tk \
        tesseract-ocr \
        tesseract-ocr-fas

WORKDIR /tmp

COPY ./requirements.txt /tmp/requirements.txt
RUN python3 -m venv /py && \
  /py/bin/pip install --upgrade pip && \
  /py/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \
  rm /tmp/requirements.txt


WORKDIR /app

ENV PATH="/py/bin:$PATH"
