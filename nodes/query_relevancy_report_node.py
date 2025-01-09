from nodes.agent_state import AgentState


def query_relevancy_report(state: AgentState) -> AgentState:
    print("--- QUERY RELEVANCY REPORT ---")

    return {
        "reports": f"Your query does not seem to be relevant to the database {state['db_info']['db_name']}. Please let me know what specific information you're looking for so I can assist you better"
    }