import json
import duckdb
from io import StringIO
import pandas as pd
from langgraph.graph import START, StateGraph, END
from langgraph.graph.graph import CompiledGraph
from nodes.generate_column_description_node import generate_column_description
from nodes.configure_new_dataset_node import configure_new_dataset
from  nodes.file_manager_db import if_db_exist, get_db_info_by_dataset
from nodes.db_state import DBState


def generate_graph()-> CompiledGraph:
    
    workflow = StateGraph(DBState)
    workflow.add_node("generate_column_description", generate_column_description)
    workflow.add_node("configure_new_dataset", configure_new_dataset)

    workflow.add_edge(START, "generate_column_description")
    workflow.add_edge("generate_column_description", "configure_new_dataset")
   
    workflow.add_edge("configure_new_dataset", END)

    graph = workflow.compile()
    
    return graph

def execute_graph(dataset_name, parquet_file_path):
    db_info = get_db_info_by_dataset(dataset_name)
    if db_info:
        # df_from_json_string = pd.read_csv(StringIO(db_info.df_head)) 
        data = json.loads(db_info.df_head)
        df = pd.DataFrame.from_dict(data)

        data = {
            "dataset_name": db_info.dataset_name, 
            "db_name":db_info.duck_db_path, 
            "table_name": db_info.table_name, 
            "column_descriptions": db_info.column_descriptions,
            "data_frame": df,
            "db_creation_error": json.dumps({"success": True, "message": f"Dataset '{dataset_name}' already exist."})
        }
        
        return data
        
    
    db_name = f'data/{dataset_name.replace(" ", "_")}'
    db_name = db_name.lower()
    table_name = f'{dataset_name.replace(" ", "_")}_table'
    table_name =table_name.lower()
    
    conn_in_memory = duckdb.connect(':memory:')
    conn_in_memory.sql(f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{parquet_file_path}');")
    df = conn_in_memory.execute(f'''  
        SELECT 
            *
        FROM
        {table_name}
        Limit 10
        ''').df()

    conn_in_memory.close()
    graph = generate_graph()
    return graph.invoke({"dataset_name": dataset_name, "db_name":db_name, "table_name": table_name, "data_frame": df})