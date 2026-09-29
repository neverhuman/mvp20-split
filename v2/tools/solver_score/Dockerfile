# Build from an offline wheelhouse containing this tool and its declared dependency closure.
# Supply a reviewed digest-pinned Python 3.12 base; record the resulting image digest separately.
ARG PYTHON_BASE
FROM ${PYTHON_BASE}
COPY wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels amphora-solver-score==0.1.0
USER 65532:65532
ENTRYPOINT ["python", "-m", "amphora_solver_score"]
CMD ["compute"]
