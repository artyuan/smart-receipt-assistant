import psycopg2
from psycopg2 import sql, OperationalError, DatabaseError
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from src.sql_commands import sql_commands
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from src.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
import pandas as pd
from sqlalchemy import create_engine

def create_postgres_database(db_name, host, port, user, password):
    # Connect to PostgreSQL server
    conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)

    # Set the connection to autocommit transactions
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Create a cursor object using the cursor() method
    cursor = conn.cursor()

    try:
        cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db_name)))
        print(f"Database {db_name} dropped successfully (if it existed).")
    except psycopg2.Error as e:
        print(f"An error occurred while dropping the database: {e}")
        # If we can't drop the database, we shouldn't continue trying to create it
        cursor.close()
        conn.close()
        return

    # Create a new database
    try:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_name)))
        print(f"Database {db_name} created successfully.")
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

def execute_sql(connection, sql_script):
    cursor = connection.cursor()
    try:
        cursor.execute(sql_script)
        connection.commit()
        print("Query executed successfully")
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()

def run_sql_commands(db_name, host, port, user, password, sql_commands):
    conn = None
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("Connection established successfully.")

        # Execute each SQL command
        for n, command in enumerate(sql_commands):
            try:
                print(f"Executing command {n + 1}/{len(sql_commands)}...")
                execute_sql(conn, command)
            except DatabaseError as e:
                print(f"Error executing SQL command #{n + 1}: {e}")

    except OperationalError as conn_err:
        print(f"Database connection error: {conn_err}")

    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

def get_database_url():
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_sql_database():
    return SQLDatabase.from_uri(get_database_url())

def insert_sql_query(query: str):
    try:
        run_sql_commands(DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, [query])
    except Exception as e:
        print(f'Error: {e}')
        raise


def create_db_engine():
    """Creates a PostgreSQL SQLAlchemy engine."""
    try:
        engine = create_engine(
            f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        )
        return engine
    except Exception as e:
        raise ConnectionError("Failed to create database engine") from e


def load_invoice_data(engine) -> pd.DataFrame:
    """Loads invoice data from the PostgreSQL database."""
    try:
        query = "SELECT * FROM invoices;"
        df = pd.read_sql(query, engine)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
    except Exception as e:
        raise RuntimeError("Failed to load or parse data from the database") from e

if __name__ == '__main__':
    # Create database
    create_postgres_database(DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
    run_sql_commands(DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, sql_commands)


