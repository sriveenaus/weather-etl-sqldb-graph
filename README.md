# weather-etl-sqldb-graph
Production-Grade Data Engineering Mini-Project.     Code is modular (weather_data.py and visualize.py).      Environment is consistent (Docker).      Orchestration is simple (docker-compose).      Data is persistent and accessible (/output).



--------------------------------------------------------------------------------
SUMMARY
--------------------------------------------------------------------------------

This task asks an agent to build a weather data ETL pipeline that stores
processed records in SQLite and Parquet formats, then generates a temperature
trend line chart. The task uses docker-compose, making it a multi-container
task. However, the docker-compose.yaml is non-functional in the harbor harness
(hardcoded paths instead of harness variables), the oracle solution is directly
exposed to the agent via a broad COPY in the Dockerfile, the multi-container
metadata flags are absent from task.toml, and the ETL script fetches live data
from an external web API rather than using pre-bundled data files.

<img width="1081" height="833" alt="Screenshot from 2026-03-10 15-36-56" src="https://github.com/user-attachments/assets/5102b409-af4f-4f67-bf4a-f37113cace2b" />


================================================================================
                            CRITICAL ISSUES ❌
================================================================================

--------------------------------------------------------------------------------
1. docker-compose.yaml Uses Hardcoded Paths — Missing All Harness Variables
--------------------------------------------------------------------------------

File:    tbench-task/environment/docker-compose.yaml (lines 1–11)
Problem: The docker-compose.yaml uses hardcoded relative paths and omits every
         required harness environment variable. It also contains a YAML syntax
         error on line 7 (no space after the key `command:`). As written, this
         file is entirely non-functional in the harbor harness.

Current code:
┌─────────────────────────────────────────────────────────────────────────────┐
│  services:                                                                  │
│    main:                                                                    │
│      build:                                                                 │
│        context: ..                                                          │
│        dockerfile: environment/Dockerfile                                   │
│        command:bash /app/solution/solve.sh   # ← YAML syntax error         │
│      volumes:                                                               │
│        - ../output:/app/output                                              │
│        - ../logs:/logs                                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Required fix:
┌─────────────────────────────────────────────────────────────────────────────┐
│  services:                                                                  │
│    main:                                                                    │
│      build:                                                                 │
│        context: ${CONTEXT_DIR}                                              │
│      image: ${MAIN_IMAGE_NAME}                                              │
│      command:                                                               │
│        - sh                                                                 │
│        - -c                                                                 │
│        - sleep infinity                                                     │
│      environment:                                                           │
│        - TEST_DIR=${TEST_DIR}                                               │
│      volumes:                                                               │
│        - ${HOST_VERIFIER_LOGS_PATH}:${ENV_VERIFIER_LOGS_PATH}              │
│        - ${HOST_AGENT_LOGS_PATH}:${ENV_AGENT_LOGS_PATH}                    │
│      deploy:                                                                │
│        resources:                                                           │
│          limits:                                                            │
│            cpus: ${CPUS}                                                    │
│            memory: ${MEMORY}                                                │
│  networks:                                                                  │
│    app-network:                                                             │
│      driver: bridge                                                         │
└─────────────────────────────────────────────────────────────────────────────┘

Explanation: The harbor harness substitutes ${CONTEXT_DIR}, ${MAIN_IMAGE_NAME},
${HOST_VERIFIER_LOGS_PATH}, ${ENV_VERIFIER_LOGS_PATH}, ${HOST_AGENT_LOGS_PATH},
${ENV_AGENT_LOGS_PATH}, ${CPUS}, and ${MEMORY} at runtime. Hardcoded paths like
`context: ..` and `../logs:/logs` are unknown to the harness and will cause the
compose orchestration to fail entirely.

--------------------------------------------------------------------------------
2. Dockerfile Exposes Oracle Solution to Agent + ENTRYPOINT Auto-Runs It
--------------------------------------------------------------------------------

File:    tbench-task/environment/Dockerfile (lines 12–18)
         tbench-task/environment/docker-compose.yaml (line 4)
Problem: The docker-compose.yaml sets `context: ..` (the task root), so the
         Dockerfile's `COPY . /app` copies solution/, tests/, instruction.md,
         and task.toml into /app — fully visible to the agent. Additionally,
         the ENTRYPOINT auto-runs solve.sh at container start, preventing the
         agent from having an idle workspace. task.toml also has a non-standard
         `[image]` section with `copy_dir = "solution"` that further encodes
         solution copying into the build.

Current code:
┌─────────────────────────────────────────────────────────────────────────────┐
│  # Dockerfile                                                               │
│  COPY . /app                          # copies solution/ and tests/         │
│  ENTRYPOINT ["/bin/bash", "/app/solve.sh"]  # auto-runs oracle solution     │
│                                                                             │
│  # task.toml [image] section                                                │
│  [image]                                                                    │
│  copy_dir = "solution"                # explicitly copies solution in       │
└─────────────────────────────────────────────────────────────────────────────┘

Required fix:
┌─────────────────────────────────────────────────────────────────────────────┐
│  # Dockerfile — use environment/ as build context and copy only task data   │
│  FROM python:3.11-slim                                                      │
│  WORKDIR /app                                                               │
│  RUN pip install pandas==2.2.2 requests==2.32.3 click==8.1.7 \             │
│          pyarrow==17.0.0 matplotlib==3.9.2                                  │
│  COPY app/ /app/                  # copy only task scripts, not solution    │
│  CMD ["bash"]                     # idle; agent drives execution            │
│                                                                             │
│  # Remove [image] section from task.toml entirely                          │
└─────────────────────────────────────────────────────────────────────────────┘

Explanation: The oracle solution must never be visible to the agent. The harness
provides solution/ and tests/ automatically at the correct paths. The main
container must also stay idle (sleep infinity / bash) so the agent can work
interactively; auto-running the solution via ENTRYPOINT bypasses agent
evaluation entirely.

--------------------------------------------------------------------------------
3. Missing Multi-Container Metadata Flags in task.toml
--------------------------------------------------------------------------------

File:    tbench-task/task.toml (lines 3–10)
Problem: A docker-compose.yaml exists in environment/, making this a multi-
         container task. The required flags `is_multi_container = true` and
         `custom_docker_compose = true` are absent from the [metadata] section.
         Without these flags the harness will not use the docker-compose.yaml
         and will fall back to single-container mode, ignoring the compose
         configuration entirely.

Current code:
┌─────────────────────────────────────────────────────────────────────────────┐
│  [metadata]                                                                 │
│  author_name = "Veena Rao"                                                  │
│  author_email = "sriveena.us@gmail.com"                                     │
│  difficulty = "medium"                                                      │
│  category = "data-processing"                                               │
│  tags = [ "file-operations",]                                               │
└─────────────────────────────────────────────────────────────────────────────┘

Required fix:
┌─────────────────────────────────────────────────────────────────────────────┐
│  [metadata]                                                                 │
│  author_name = "Veena Rao"                                                  │
│  author_email = "sriveena.us@gmail.com"                                     │
│  difficulty = "medium"                                                      │
│  category = "data-processing"                                               │
│  tags = [ "file-operations" ]                                               │
│  is_multi_container = true                                                  │
│  custom_docker_compose = true                                               │
└─────────────────────────────────────────────────────────────────────────────┘

Explanation: Per the T-Bench 2.0 spec, any task that ships a docker-compose.yaml
must declare both flags in [metadata] so the harness activates compose-based
orchestration.

--------------------------------------------------------------------------------
4. Solution Fetches Live Data from an External Web API
--------------------------------------------------------------------------------

File:    tbench-task/environment/app/weather_data.py (lines 8, 21–22)
Problem: The ETL script calls a live external API at runtime
         (archive-api.open-meteo.com). This violates the T-Bench guideline
         against fetching data from the web: the endpoint can change, go down,
         or return different data over time, making the task non-reproducible
         and non-deterministic across runs or hardware environments.

Current code:
┌─────────────────────────────────────────────────────────────────────────────┐
│  API_URL = "https://archive-api.open-meteo.com/v1/archive"                 │
│  ...                                                                        │
│  response = requests.get(API_URL, params=params)                            │
│  response.raise_for_status()                                                │
│  return response.json()                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

Required fix:
┌─────────────────────────────────────────────────────────────────────────────┐
│  # Pre-download the JSON response and save as environment/weather_raw.json  │
│  # Then load it in the script:                                              │
│  with open('/app/weather_raw.json') as f:                                  │
│      return json.load(f)                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

Explanation: Weather data for the fixed date range 2024-01-01 to 2024-01-10
should be downloaded once and stored as a static file in environment/. The
Dockerfile can then COPY it into /app so the solution works identically on any
machine without network access.

================================================================================
                            OVERALL ASSESSMENT
================================================================================

This task has a clear and realistic concept — an ETL pipeline writing to SQLite
and Parquet with a visualization — but every layer of the execution stack
contains a blocking defect: the compose file is non-functional, the oracle
solution is exposed and auto-executed, the multi-container harness flags are
absent, and the data source is a live external API. The task requires
substantial rework before it can be used for evaluation.

Key Strengths:
  ✓ Coherent, realistic task concept covering ETL, persistence, and plotting
  ✓ All six required files are present
  ✓ Test suite covers the three main output artifacts (DB, Parquet, PNG)

Key Weaknesses:
  ✗ docker-compose.yaml is non-functional; missing all required harness vars
  ✗ Oracle solution is fully exposed to the agent via Dockerfile COPY
  ✗ Solution depends on a live external API, breaking reproducibility

Evaluates: ETL pipeline implementation, multi-format data persistence,
           data visualization, Docker/compose configuration

================================================================================
  RECOMMENDATION: ❌ REQUIRES FIXES

  All four critical issues must be resolved before this task can be used.https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax
  The docker-compose.yaml, Dockerfile, task.toml metadata, and data-sourcing
  strategy all need to be rebuilt to conform to T-Bench 2.0 standards.
================================================================================
