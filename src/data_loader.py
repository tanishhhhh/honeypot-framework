import pandas as pd
import duckdb
import os


# Default path to the DuckDB dataset file
DB_PATH = os.getenv(
    "DB_PATH",
    r"C:\TANISH WORK\Msc CS\Semester 03\Reserach Paper\CTU Hornet 65 Niner A Network Dataset of Geographically Distributed Low-Interaction Honeypots\CTU-Hornet-65-Niner\duckdb\ctu-hornet-65-niner_v0.1.db",
)


def load_data(filepath: str = DB_PATH) -> pd.DataFrame:
    """
    Loads the honeypot dataset directly from a DuckDB database file.

    Selects only the columns required for feature engineering and model
    training, and applies dtype optimisation to reduce memory usage.

    Args:
        filepath (str): Absolute path to the DuckDB ``.db`` file.
                        Defaults to the ``DB_PATH`` environment variable
                        (or the hard-coded project path).

    Returns:
        pd.DataFrame: The loaded dataset with columns
            ``duration``, ``orig_bytes``, ``resp_bytes``, ``orig_pkts``,
            ``resp_pkts``, ``proto``, ``conn_state``, ``history``.

    Raises:
        FileNotFoundError: If the database file does not exist.
    """
    print(f"Attempting to load data from: {filepath}")

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Database file not found at: {filepath}\n"
            "Set the DB_PATH environment variable or pass the correct path."
        )

    # Connect in read-only mode to avoid accidental writes
    con = duckdb.connect(filepath, read_only=True)

    # Discover available tables
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    print(f"Tables found in database: {table_names}")

    if not table_names:
        con.close()
        raise ValueError("No tables found in the DuckDB database.")

    table = table_names[0]
    print(f"Loading data from table: '{table}'")

    # Select only the columns needed for feature engineering / training
    query = f"""
        SELECT duration, orig_bytes, resp_bytes,
               orig_pkts, resp_pkts,
               proto, conn_state, history
        FROM "{table}"
    """

    df = con.execute(query).df()
    con.close()

    # ── Dtype optimisation to reduce memory footprint ──
    df["orig_bytes"] = pd.to_numeric(df["orig_bytes"], errors="coerce").fillna(0).astype("int32")
    df["resp_bytes"] = pd.to_numeric(df["resp_bytes"], errors="coerce").fillna(0).astype("int32")
    df["orig_pkts"]  = pd.to_numeric(df["orig_pkts"],  errors="coerce").fillna(0).astype("int16")
    df["resp_pkts"]  = pd.to_numeric(df["resp_pkts"],  errors="coerce").fillna(0).astype("int16")

    print(f"Data loaded successfully — {len(df):,} rows, {len(df.columns)} columns.")
    return df


if __name__ == "__main__":
    df = load_data()

    print("\nDataset Shape:")
    print(df.shape)

    print("\nColumn Dtypes:")
    print(df.dtypes)

    print("\nDataset Head:")
    print(df.head())
