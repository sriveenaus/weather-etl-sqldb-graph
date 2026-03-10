import pandas as pd
import requests
import sqlite3
import click
import os

# Configuration
API_URL = "https://archive-api.open-meteo.com/v1/archive"
DB_NAME = "output/weather_data.db"
OUTPUT_DIR = "output/weather_parquet_store"

def fetch_weather_data(start_date, end_date, lat=40.71, lon=-74.00):
    """Fetches hourly weather data from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m",
    }
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    return response.json()

def process_data(json_data):
    """Normalizes, interpolates, and aggregates data."""
    # 1. Normalize into DataFrame
    hourly_data = json_data['hourly']
    df = pd.DataFrame(hourly_data)
    
    # 2. Standardize field names
    df = df.rename(columns={
        'time': 'timestamp',
        'temperature_2m': 'temp_c',
        'relative_humidity_2m': 'humidity_pct'
    })
    
    # 3. Handle missing values via linear interpolation
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    df = df.interpolate(method='linear')
    
    # 4. Create partitioning columns
    df['year_month'] = df.index.strftime('%Y-%m')
    df['date'] = df.index.date
    
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

    # --- EXTRACT ---
    raw_json = fetch_weather_data(start, end)
    
    # --- TRANSFORM ---
    full_df = process_data(raw_json)
    daily_summary_df = aggregate_daily(full_df)
    
    # --- LOAD ---
    # A. Write to Monthly Parquet Files (Partitioned)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    full_df.to_parquet(
        OUTPUT_DIR, 
        partition_cols=['year_month'], 
        engine='pyarrow', 
        index=True
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
