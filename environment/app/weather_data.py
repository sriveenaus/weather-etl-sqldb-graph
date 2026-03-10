import pandas as pd
import sqlite3
import click
import os
import json
# Configuration
API_URL = "https://archive-api.open-meteo.com/v1/archive"
DB_NAME = "output/weather_data.db"
OUTPUT_DIR = "output/weather_parquet_store"

# 1. Download the JSON response once and commit it to environment/:        
#    environment/weather_raw.json                                          
# 2. In Dockerfile, copy it into the image:                                
#    COPY weather_raw.json /app/weather_raw.json                           
# 3. Remove the requests.get() call entirely and just read the file: 

# 1. Fix the function signature in weather_data.py  
def fetch_weather_data():
    with open("/app/weather_raw.json") as f: 
        return json.load(f)

def process_data(json_data):
    """Normalizes, interpolates, and aggregates data."""
    # 1. Normalize into DataFrame
    df = pd.DataFrame(json_data)

    # ensure correct types
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["temp_c"] = df["temp_c"].astype(float)

    return df

def aggregate_daily(df):
    """Aggregates max and min daily temps for the SQLite summary table."""
    # Group by date and get max/min as required by instruction.md
    daily_summary = df.groupby('date').agg({
        'temp_c': ['max', 'min']
    }).reset_index()
    
    # Flatten columns to match: date, temp_max, temp_min
    daily_summary.columns = ['date', 'temp_max', 'temp_min']
    
    # Ensure date is a string (TEXT) for SQLite
    daily_summary['date'] = daily_summary['date'].astype(str)
    
    return daily_summary

@click.command()
@click.option('--start', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--end', required=True, help='End date (YYYY-MM-DD)')
def run_etl(start, end):
    click.echo(f"🚀 Starting ETL for {start} to {end}...")

    #--- EXTRACT ---
    raw_json = fetch_weather_data()
    
    # --- TRANSFORM ---
    full_df = process_data(raw_json)
    daily_summary_df = aggregate_daily(full_df)
    
    # --- LOAD ---
    # A. Write to Monthly Parquet Files (Partitioned)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # weather_data.py — derive year_month before writing, or drop partitioning
    # create partition column
    full_df['year_month'] = pd.to_datetime(full_df['date']).dt.to_period('M').astype(str)
    full_df["date"] = pd.to_datetime(full_df["date"]).dt.strftime("%Y-%m-%d")
    full_df["temp_c"] = full_df["temp_c"].astype(float)
    # write parquet
    full_df.to_parquet(
        OUTPUT_DIR,
        partition_cols=["year_month"],
        index=False
    )

    click.echo(f"✅ Monthly Parquet files saved to /{OUTPUT_DIR}")

    # B. Load Daily Summary into SQLite
    conn = sqlite3.connect(DB_NAME)
    daily_summary_df.to_sql('daily_summary', conn, if_exists='replace', index=False)
    conn.close()
    click.echo(f"✅ Daily summary loaded into {DB_NAME}")
    
    click.echo("✨ ETL Task Completed Successfully.")

if __name__ == "__main__":
    run_etl()
