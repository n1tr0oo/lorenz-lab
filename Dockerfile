# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS wheels
WORKDIR /build
COPY requirements.txt .
RUN python -m pip wheel --wheel-dir /wheels -r requirements.txt \
    && python -m pip install --no-cache-dir setuptools==80.9.0 wheel==0.45.1
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip wheel --no-build-isolation --no-deps --wheel-dir /wheels .

FROM python:3.12-slim-bookworm AS base
ARG SOURCE_COMMIT=unknown
LABEL org.opencontainers.image.title="Lorenz Lab" \
      org.opencontainers.image.source="https://github.com/n1tr0oo/lorenz-lab" \
      org.opencontainers.image.revision=$SOURCE_COMMIT
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    LORENZ_SOURCE_COMMIT=$SOURCE_COMMIT
COPY --from=wheels /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels lorenz-lab \
    && rm -rf /wheels \
    && groupadd --gid 10001 research \
    && useradd --uid 10001 --gid research --create-home research \
    && mkdir -p /data /reports \
    && chown research:research /data /reports
WORKDIR /app

FROM base AS test
COPY tests ./tests
COPY tools/ci_test.py ./tools/ci_test.py
USER 10001:10001
ENTRYPOINT ["python", "/app/tools/ci_test.py", "--output", "/reports"]

FROM base AS runtime
COPY examples ./examples
COPY docs/index.html ./docs/index.html
COPY docs/assets ./docs/assets
USER 10001:10001
WORKDIR /data
ENTRYPOINT ["python", "-m", "lorenz_lab"]
CMD ["--config", "/app/examples/default.json", "--output", "/data/default"]
