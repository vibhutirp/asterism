# Store Purchase Cluster Simulation

This repo includes a Streamlit app that creates synthetic store purchase test
transactions, generates simple product images, and clusters purchase behavior
for simulation/exploration.

## Run the Streamlit app

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the app:

```powershell
python -m streamlit run app.py
```

The app lets you adjust transaction volume, number of clusters, transaction
history window, simulation age month, and random seed. It includes a
galaxy-themed 3D cluster map, aging timeline, cluster summaries, transaction
drilldowns, and a product catalog with generated images.

## Optional external insights

The `External insights` tab can search Exa and summarize the results with
OpenRouter. Provide credentials in the sidebar or set these environment
variables before starting Streamlit:

```powershell
$env:EXA_API_KEY = "your-exa-api-key"
$env:OPENROUTER_API_KEY = "your-openrouter-api-key"
$env:OPENROUTER_ACCOUNT_EMAIL = "you@example.com"
$env:OPENROUTER_MODEL = "openai/gpt-4o-mini"
```

Do not commit real API keys. If a key was pasted into a chat or log, rotate it.

## Snowflake Connection

This project connects to Snowflake with `snowflake-connector-python`.

### Setup

Install the dependency:

```powershell
python -m pip install -r requirements.txt
```

Set environment variables in PowerShell:

```powershell
$env:SNOWFLAKE_ACCOUNT = "orfaqms-gyb24946"
$env:SNOWFLAKE_USER = "SMRANGARA"
$env:SNOWFLAKE_PASSWORD = "your-password-or-token"
$env:SNOWFLAKE_WAREHOUSE = "COMPUTE_WH"
$env:SNOWFLAKE_DATABASE = "WORKFORCE_ANALYTICS"
$env:SNOWFLAKE_SCHEMA = "PUBLIC"
```

Run the connection test:

```powershell
python snowflake_connection.py
```

Do not commit real credentials. The `.env` file is ignored by Git.
