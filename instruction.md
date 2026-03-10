# Weather ETL Pipeline Task

## Objective

Build a reproducible ETL pipeline that processes the provided weather dataset and produces:

1. A SQLite database
2. A Parquet dataset
3. A PNG visualization

All outputs must be derived strictly from the provided input file.

---

## Input Data

You are provided with:

/app/weather_raw.json.

This json contains daily weather observations.

Your solution must use this file as the sole source of truth.
Hardcoded outputs or synthetic data generation is not allowed.

---

## Required Outputs

Your pipeline must produce the following artifacts:

### 1️⃣ SQLite Database

Location:
output/weather_data.db

Requirements:

- Must contain a table named: daily_summary
- Table must contain the following columns:
  - date
  - temp_max
  - temp_min
- The table must contain one row per date
- temp_max must be the maximum temperature for that date
- temp_min must be the minimum temperature for that date
- Values must be computed from /app/weather_raw.json

---

### 2️⃣ Parquet Output

Location:
output/weather_parquet_store/

Requirements:

- Must be a directory-based Parquet dataset (single-file not allowed) 
- Stores one row per hourly observation
- Schema must include:
  - date   (string, e.g. "2024-01-01")
  - temp_c (float, hourly temperature in Celsius)
- The daily_summary SQLite table is derived by aggregating 
  temp_c per date (max -> temp_max, min -> temp_min)


### 3️⃣ Visualization

Location:
output/temperature_plot.png

Requirements:

- Must be a PNG image
- Must plot temperature trends over time
- Must be generated from the aggregated daily data
- File must not be empty or blank

Alternative filenames are NOT allowed.

---

## Environment Requirements

You must include:

docker-compose.yaml

The file must contain a valid `services:` section.

---

## Implementation Constraints

- All outputs must be derived from /app/weather_raw.json.
- Hardcoded artifacts are not allowed.
- Row counts and aggregate values must match computations from the input file.
- The pipeline must be reproducible via the provided environment configuration.

---

## Expected Workflow

1. Read /app/weather_raw.json
2. Compute daily min and max temperatures
3. Save results to:
   - SQLite database (daily_summary table)
   - Parquet dataset (weather_parquet_store/)
4. Generate temperature_plot.png from aggregated data
5. Ensure docker-compose.yaml is present in app/

---

## Evaluation Criteria

Your submission will be validated for:

- Correct output paths
- Correct schema
- Correct aggregation logic
- Output consistency across formats
- Proper environment configuration
- Reproducibility
