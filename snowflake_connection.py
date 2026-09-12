import os

import snowflake.connector


def connect_to_snowflake():
    """Create a Snowflake connection from environment variables."""
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "WORKFORCE_ANALYTICS"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
    )


def main():
    with connect_to_snowflake() as ctx:
        with ctx.cursor() as cur:
            cur.execute("SELECT CURRENT_VERSION()")
            version = cur.fetchone()[0]
            print(f"Connected to Snowflake. Version: {version}")


if __name__ == "__main__":
    main()
