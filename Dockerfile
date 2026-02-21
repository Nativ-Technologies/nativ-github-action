FROM python:3.12-slim

RUN pip install --no-cache-dir "nativ>=0.2.0" PyYAML && \
    apt-get update && apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY translate_json.py translate_yaml.py translate_po.py translate_lines.py /
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
