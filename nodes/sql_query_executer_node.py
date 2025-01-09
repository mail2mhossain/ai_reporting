from sqlalchemy import create_engine
import pandas as pd
from langchain_core.messages import FunctionMessage
from langgraph.types import Command
from nodes.nodes_name import CHECK_SQL_DECISION
from nodes.agent_state import AgentState


def execute_sql_query(state: AgentState):
    print("--- EXECUTE SQL QUERY ---")
    
    sql_query = state["SQL_query"]
        
    engine = create_engine(state["db_info"]["connection_string"])
        
    try:
        df = pd.read_sql_query(sql_query, engine)
        return Command(
            update = {
                "data_frame": df,
                "SQL_error": None,
            },
            goto = CHECK_SQL_DECISION
        )   
    
    except Exception as e:
        print(f"SQL Execution Error: {e}")
        return Command(
            update = {
                "data_frame": None,
                "SQL_error": str(e),
                # "sanitize_check": 0
            },
            goto = CHECK_SQL_DECISION
        )   
    finally:
        engine.dispose() 
    
    


# results = execute_sql_query({"SQL_query": "SELECT * FROM public.actor LIMIT 10"})

# if results["data_frame"] is not None:
#     print(results["data_frame"])
# else:
#     print(results["SQL_error"])