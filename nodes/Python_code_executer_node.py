import pandas as pd
from langgraph.graph import END
from langchain_experimental.tools.python.tool import PythonAstREPLTool, PythonREPLTool
from langgraph.types import Command
from nodes.agent_state import AgentState
from nodes.nodes_name import REPORT_GENERATION_DECISION

def run_python_code(state: AgentState) -> AgentState:
    print("--- PYTHON CODE EXECUTER ---")
    try: 
        Python_script = state['Python_Code']
        
        df = state["data_frame"]
        df_locals={}
        df_locals["df"] = df
        python_repl = PythonAstREPLTool(locals=df_locals)
    
    
        results = python_repl.run(Python_script)     
        if "error:" in results.lower():
            return Command(
                update={
                    "execution_error": results
                },
                goto=REPORT_GENERATION_DECISION
            ) 
        else:
            print(f"Execution Results:\n{results}")
            # with open("reports_from_python.md", "w") as file:
            #     file.write(results)
            return Command(
                update={
                    "execution_results": results,
                    "execution_error": None
                },
                goto=REPORT_GENERATION_DECISION
            ) 
    except Exception as e:
        return Command(
            update={
                "execution_error": str(e)
            },
            goto=REPORT_GENERATION_DECISION
        ) 