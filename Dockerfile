# Use slim instead of alpine (faster builds).
FROM python:3.8-slim

# Create work directory.
WORKDIR /code

# Copy files (unnecessary files excluded via .dockerignore).
COPY . .

# Download and make trec_eval.
RUN apt-get update && \
    apt-get install git -y && \
    apt-get install build-essential -y && \
    git clone https://github.com/usnistgov/trec_eval.git && \
    cd trec_eval && make && cd .. && \
    pip install -r requirements.txt

# Expose port.
EXPOSE 8050

# Start dashboard app.
CMD [ "python", "./run-comparator/app.py" ]
