import os
import duckdb
from nodes.file_manager_db import get_db_info_by_dataset, insert_db_info

def load_new_data(dataset_name, parquet_file_path):
    print("--- LOADING NEW DATA ---")
    
    db_info = get_db_info_by_dataset(dataset_name)

    if db_info is None:
        message = {"success": False, "message": f"A dataset with the name '{dataset_name}' does not exist."}
        return message
    
    db_name = db_info.duck_db_path
    table_name = db_info.table_name
    file_name = os.path.basename(parquet_file_path)

    conn_persistent = duckdb.connect(db_name)
    total_rows = conn_persistent.execute(f"SELECT COUNT(*) FROM '{parquet_file_path}'").fetchone()[0]
    table_exists = conn_persistent.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}'").fetchone()[0]

    if table_exists:
        conn_persistent.execute(f"INSERT INTO {table_name} SELECT * FROM '{parquet_file_path}'")
    else:
        conn_persistent.execute(f"CREATE TABLE {table_name} AS SELECT * FROM '{parquet_file_path}'")
    
    insert_db_info(dataset_name, file_name, total_rows, 0, total_rows)

    conn_persistent.close()
    os.remove(parquet_file_path)

    message = {
        "success": True,
        "total_rows": total_rows,
        "message": f"Successfully loaded {total_rows} rows into the database.",
    }
    
    return message