from langgraph.types import Command
from nodes.file_manager_db import get_db_info_by_dataset
from nodes.agent_state import AgentState 
from nodes.nodes_name import CHECK_QUERY_RELEVANCY

def get_dataset_detail(state: AgentState) -> AgentState:
    print("--- GET DATASET DETAIL ---")
    db_name = state["db_name"]
    db_info = get_db_info_by_dataset(db_name)

    return Command(
        update={
            "db_info": db_info
        },
        goto=CHECK_QUERY_RELEVANCY
    ) 