import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables

class DBManager:
    """
    Manages PostgreSQL database connections and data fetching.
    """
    def __init__(self):
        self.conn = None
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_name = os.getenv("DB_NAME", "customer_db")
        self.db_user = os.getenv("DB_USER", "user")
        self.db_password = os.getenv("DB_PASSWORD", "password")
        self._connect_on_demand() # Initial connection attempt

    def _connect_on_demand(self):
        """Connects to the database if not already connected or if connection is closed."""
        if not self.conn or self.conn.closed:
            try:
                self.conn = psycopg2.connect(
                    host=self.db_host,
                    database=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    connect_timeout=10 # Add a timeout for connection attempts
                )
                print(f"Connected to PostgreSQL: {self.db_user}@{self.db_host}/{self.db_name}")
            except psycopg2.OperationalError as e:
                print(f"OperationalError: Could not connect to PostgreSQL. Is the database running and accessible? Error: {e}")
                self.conn = None # Ensure conn is None on failed connection
                raise
            except Exception as e:
                print(f"Unexpected error connecting to PostgreSQL: {e}")
                self.conn = None
                raise

    def fetch_data_as_df(self, query: str, params: tuple = None) -> pd.DataFrame:
        """
        Executes a SQL query and returns the results as a Pandas DataFrame.
        Ensures connection is open before executing.
        """
        self._connect_on_demand()
        try:
            df = pd.read_sql(query, self.conn, params=params)
            return df
        except Exception as e:
            print(f"Error executing query: {query} with params {params}. Error: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None):
        """
        Executes a non-SELECT SQL query (e.g., INSERT, CREATE).
        Ensures connection is open before executing.
        """
        self._connect_on_demand()
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
            self.conn.commit()
            print(f"Query executed successfully: {query[:50]}...") # Log part of the query
        except Exception as e:
            self.conn.rollback() # Rollback on error
            print(f"Error executing non-SELECT query: {query[:50]}... Error: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            print("PostgreSQL connection closed.")

# Instantiate DBManager globally to manage connections
db_manager = DBManager()
