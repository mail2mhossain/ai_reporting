from langgraph.graph import END
from typing_extensions import TypedDict, Literal
from langgraph.types import Command, Interrupt, StreamProtocol
from nodes.agent_state import AgentState
from nodes.nodes_name import (
    RE_GENERATE_SQL_QUERY,
    REPORT_TYPE,
    SQL_QUERY_EXECUTION_ERROR_REPORT
)

def make_sql_decision(state:AgentState) ->  Command[Literal[ SQL_QUERY_EXECUTION_ERROR_REPORT, RE_GENERATE_SQL_QUERY, REPORT_TYPE ]]:
    print("--- MAKING DECISION AFTER SQL EXECUTION ---")
    sql_generation_try = state['sql_generation_try']
    max_sql_generation_try = state['max_sql_generation_try']
    SQL_error = state['SQL_error']

    if SQL_error:
        if sql_generation_try >= max_sql_generation_try:
            return Command(
                goto=SQL_QUERY_EXECUTION_ERROR_REPORT
            )   
        else:
            sql_generation_try = sql_generation_try + 1
            # state.update({
            #     "sql_generation_try": sql_generation_try,
            # })
            print(f"SQL Generation Try: {sql_generation_try}")
            return Command(
                update={
                    "sql_generation_try": sql_generation_try,
                    # update the message history
                    # "messages": [ToolMessage("Successfully looked up user information", tool_call_id=tool_call_id)]
                },
                goto=RE_GENERATE_SQL_QUERY
            )
    else:
        print(f"Get Report Type: {REPORT_TYPE}")
        return Command(
            goto = REPORT_TYPE
        )    