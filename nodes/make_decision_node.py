from typing_extensions import TypedDict, Literal
from langgraph.types import Command, Interrupt, StreamProtocol
from langgraph.graph import END
from nodes.agent_state import AgentState
from nodes.nodes_name import (
    PYTHON_CODE_RE_GENERATION,
    REPORT_GENERATOR,
    REPORTS_COMBINER
)


def make_decision(state: AgentState) -> Literal[ REPORT_GENERATOR, PYTHON_CODE_RE_GENERATION ]:
    print("--- MAKING DECISION ---")
    execution_error = state.get("execution_error", None)
    Python_script_check = state['Python_script_check']
    max_Python_script_check = state['max_Python_script_check']

    if execution_error:
        if Python_script_check >= max_Python_script_check:
            print(f"------ Go to {END},  BCOZ {Python_script_check} times tried and failed -------")
            return Command(
                goto=END
            )  
        else:
            Python_script_check = Python_script_check + 1
            # state.update({
            #     "Python_script_check": Python_script_check,
            # })
            print(f"Execution Error: {execution_error} - {Python_script_check} times")
            print(f"------ Go to {PYTHON_CODE_RE_GENERATION} ------")
            return Command(
                update={
                    "Python_script_check": Python_script_check,
                },
                goto=PYTHON_CODE_RE_GENERATION
            ) 
    else:
        print(f"------ Go to {REPORT_GENERATOR} ------")
        return Command(
            goto=REPORT_GENERATOR
        ) 