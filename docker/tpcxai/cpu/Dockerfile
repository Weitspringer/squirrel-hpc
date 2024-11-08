# TPCx-AI 2.0.0 Docker Image (CPU only)
# Ubuntu 20.04 base image
FROM ubuntu:20.04

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-8-jdk \
    python3 \
    python3-pip \
    gnupg2 \
    curl \
    zip \
    unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Anaconda
RUN curl -LO https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh && \
    bash Anaconda3-2024.06-1-Linux-x86_64.sh -b -p /opt/conda && \
    rm Anaconda3-2024.06-1-Linux-x86_64.sh

# Set environment variables for Anaconda
ENV PATH=/opt/conda/bin:$PATH

# Run conda init
RUN conda init

# Install required libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libsndfile1 \
    libsndfile-dev && \
    rm -rf /var/lib/apt/lists/*

# Install sbt if necessary for Scala
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list && \
    curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x99E82A75642AC823" | apt-key add - && \
    apt-get update && \
    apt-get install -y sbt && \
    rm -rf /var/lib/apt/lists/*

# Copy the TPCx-AI benchmark files to the container
COPY <path-to-tpcx-ai-v2-zip> /app/tpcx-ai-v2.0.0.zip
RUN unzip /app/tpcx-ai-v2.0.0.zip -d /app && \
    rm /app/tpcx-ai-v2.0.0.zip && \
    mv /app/tpcx-ai-v2.0.0/* /app && \
    rm -r /app/tpcx-ai-v2.0.0

# Set the working directory to the root of the TPCx-AI directory
WORKDIR /app
