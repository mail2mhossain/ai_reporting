import os
import json
import duckdb 
from nodes.db_state import DBState
# from nodes.file_manager_db import insert_file_info


def add_column_if_not_exists(conn, table_name, column_name, column_type):
    # Check if the column already exists in the table
    query = f"""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' AND column_name = '{column_name}'
    """
    column_exists = conn.execute(query).fetchone()[0] > 0
    
    # Add the column only if it does not exist
    if not column_exists:
        alter_table_query = f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type}
        """
        conn.execute(alter_table_query)
        print(f"Column '{column_name}' added to table '{table_name}'.")
    else:
        print(f"Column '{column_name}' already exists in table '{table_name}'.")


def configure_new_dataset(state: DBState)-> DBState:
    print("--- CONFIGURE NEW Database ---")
    
    column_descriptions = state["column_descriptions"]
    dataset_name = state["dataset_name"]
    # parquet_file_path = state["parquet_file_path"]
    db_name = f'{state["db_name"]}.duckdb'
    table_name = state["table_name"]
    df = state["data_frame"]

    json_string = df.to_json()
    print(f'Data Frame: {json_string}')
    # message = insert_file_info(dataset_name, db_name, table_name, column_descriptions, json_string)

    # db_creation_result = json.loads(message)
    # if db_creation_result['success']:
    #     conn_persistent = duckdb.connect(db_name)
    #     conn_persistent.close()

    # return {
    #     "db_name": db_name,
    #     "table_name": table_name,
    #     "db_creation_error": message
    # }

