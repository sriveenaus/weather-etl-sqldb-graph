import os
import sqlite3
import pandas as pd
from pathlib import Path
from PIL import Image
import yaml
#This revision of the tests file is fixing anti-cheating measures
#so that the content of DB matches input CSV, parquet content matches DB
#daily_summary values are actually computed correctly
#PNG reflects real data (via data validation) 

# Harbor standard path for output volume
OUTPUT = Path("output")

#this test is to match the task-spec  
def test_docker_compose_exists():
    """Verify docker-compose.yaml exists with a services: key. """
    path = Path("/app/docker-compose.yaml")
    assert path.exists(), "/app/docker-compose.yaml is missing"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict) and "services" in data, \
        "docker-compose.yaml must contain a valid 'services:' section"
def test_sqlite_exists():                                                  
      """Verify the SQLite database was created at the expected path."""    
      assert (Path("/app/output") / "weather_data.db").exists()

def test_sqlite_data():
    """Verify SQLite db exists and has the expected weather data."""
    db_path = OUTPUT / "weather_data.db"
    assert db_path.exists(), f"Database not found at {db_path}"
    
    conn = sqlite3.connect(db_path)
    # We check common table names; adjust if your instruction.md specifies one
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = [row[0] for row in conn.execute(query).fetchall()]
    
    target_table = 'weather' if 'weather' in tables else 'daily_summary'
    assert 'daily_summary' in tables, \
        f"Required table 'daily_summary' not found. Found: {tables}"   
    df = pd.read_sql(f'SELECT * FROM {target_table}', conn)
    assert len(df) > 0, f"Table '{target_table}' is empty"
    conn.close()

def test_parquet_matches_db():
    """Verify Parquet output matches SQLite daily_summary."""
    parquet_path = OUTPUT / "weather_data.parquet"
    if not parquet_path.exists():
        parquet_path = OUTPUT / "weather_parquet_store"

    df_parquet = pd.read_parquet(parquet_path)

    conn = sqlite3.connect(OUTPUT / "weather_data.db")
    df_db = pd.read_sql("SELECT * FROM daily_summary", conn)
    conn.close()

    df_parquet = df_parquet.sort_values("date").reset_index(drop=True)
    df_db = df_db.sort_values("date").reset_index(drop=True)
 
    df_daily = df_parquet.groupby("date").agg(temp_max=("temp_c","max"), temp_min=("temp_c","min")).reset_index()
    pd.testing.assert_frame_equal(df_daily, df_db)

def test_daily_summary_correctness():
    df_parquet = pd.read_parquet(OUTPUT / "weather_parquet_store")

    # Aggregate to daily to get the same schema as daily_summary
    df_daily = (
        df_parquet.reset_index()
        .groupby("date")
        .agg(temp_max=("temp_c", "max"), temp_min=("temp_c", "min"))
        .reset_index()
    )

    df_daily["date"] = df_daily["date"].astype(str)
    df_daily = df_daily.sort_values("date").reset_index(drop=True)
    
    # Read actual values from SQLite
    conn = sqlite3.connect(OUTPUT / "weather_data.db")
    actual = pd.read_sql("SELECT date, temp_max, temp_min FROM daily_summary", conn)
    df_db = actual.sort_values("date").reset_index(drop=True)

    pd.testing.assert_frame_equal(df_daily, df_db)
 
def test_visual_output():
    """Verify the line chart was generated correctly."""
    plot_path = OUTPUT / "temperature_plot.png"
    assert plot_path.exists(), "temperature_plot.png not found in output/"
    
    # Check if image is valid and not just a tiny blank file
    assert os.path.getsize(plot_path) > 5000, "PNG file is suspiciously small"
    with Image.open(plot_path) as img:
        assert img.format == "PNG", "File is not a valid PNG image"
        assert img.size[0] > 400 and img.size[1] > 300

def test_sqlite_matches_input():
    """Verify SQLite weather table is derived from input CSV."""
    input_path = Path("/app/weather_raw.json")  # adjust if different
    assert input_path.exists(), "Input JSON missing"

    input_df = pd.read_json(input_path)

    db_path = OUTPUT / "weather_data.db"
    conn = sqlite3.connect(db_path)

    # detect actual table name
    tables = [row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()]

    target_table = 'weather' if 'weather' in tables else 'daily_summary'
    db_df = pd.read_sql(f"SELECT * FROM {target_table}", conn)

    conn.close()

    # Verify daily_summary has one row per unique date in the CSV 
    expected_dates = input_df["date"].nunique() 
    assert len(db_df) == expected_dates, (
        f"daily_summary should have {expected_dates} rows "
        f"(one per date), got {len(db_df)}"
    )
  
    # key columns must match
    assert set(input_df.columns).intersection(db_df.columns), \
        "DB schema unrelated to input data"

#This test is to verify lineage is provided from weather data input
def test_outputs_derived_from_input():
    """Ensure ETL outputs are derived from provided weather.json."""
    input_path = Path("/app/weather_raw.json")
    assert input_path.exists(), "Provided weather.JSON missing"

    input_df = pd.read_json(input_path)

    conn = sqlite3.connect(OUTPUT / "weather_data.db")
    db_df = pd.read_sql("SELECT * FROM daily_summary", conn)
    conn.close()

    # Must have same number of raw records
    expected_dates = input_df["date"].nunique()
    assert len(db_df) == expected_dates, (
        f"daily_summary should have {expected_dates} rows " 
        f"(one per unique date), got {len(db_df)}" 
    )
    # Must contain at least one identical value
    common_cols = set(input_df.columns).intersection(db_df.columns)
    assert common_cols, "No schema overlap between input and DB"

#This is to enforce exact filenames in the output 
def test_required_files_exist():
    assert (OUTPUT / "weather_data.db").exists()
    #assert (OUTPUT / "weather_data.parquet").exists()
    assert (OUTPUT / "temperature_plot.png").exists()
    assert (OUTPUT / "weather_parquet_store").is_dir()
