ARG PYTHON_BASE
FROM ${PYTHON_BASE}
COPY wheels/ /wheels/
RUN python -m pip install --no-index --find-links=/wheels amphora-synthetic-objectives==0.3.0 && rm -rf /wheels
USER 65532:65532
ENTRYPOINT ["python", "-m", "amphora_synthetic_objectives"]
