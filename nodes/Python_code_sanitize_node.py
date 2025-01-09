from typing_extensions import TypedDict, Literal
from langgraph.types import Command, Interrupt, StreamProtocol
from langgraph.graph import END
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from nodes.agent_state import AgentState
from nodes.nodes_name import (
    PYTHON_CODE_EXECUTER,
    PYTHON_CODE_RE_GENERATION,
    REPORTS_COMBINER
)
from langchain_openai import ChatOpenAI
from decouple import config

sys_msg = """
    You are an expert in Python script security. Your task is to analyze a given Python script and determine whether it is safe to execute.
    You are working with a pandas dataframe in Python. The name of the dataframe is `df`
    Consider security, unauthorized access, resource usage, external network connections, and overall intent. 
    Highlight any risky or potentially harmful sections. 
    Does this script contain any harmful or malicious elements? If so, provide a detailed explanation.
    
    Your response should be in the following format:
    {
        "is_safe": true/false,
        "reason": "<Explain why the Python script is safe or unsafe>"
    }
"""

class sanitizing_script(BaseModel):
    is_safe: bool
    reason: str

def sanitize_python_script(state:AgentState) -> Command[Literal[ PYTHON_CODE_EXECUTER, PYTHON_CODE_RE_GENERATION, END]]:
    """
    This function uses OpenAI's LLM to sanitize a given Python script, allowing only 'SAFE' execution.
    Any harmful or malicious elements will be flagged as unsafe.

    Parameters:
    script (str): The Python script to be sanitized.

    Returns:
    bool: True if the Python script is valid (safe to execute), False otherwise.
    """
    print("--- SANITIZE PYTHON SCRIPT ---")
    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    python_script = state['Python_Code']
    Python_script_check = state['Python_script_check']
    max_Python_script_check = state['max_Python_script_check']
    
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=sys_msg),
            HumanMessage(content=f"""Python script: {python_script}""")
        ]
    )

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)

    sanitize_chain = prompt | llm.with_structured_output(
        schema=sanitizing_script,
        method="function_calling",
        include_raw=False,
    )
    
    response = sanitize_chain.invoke({'input': ''})
    
    if response.is_safe == True:
        # state.update({
        #     "script_security_issues": None,
        # })
        print("------ Python script is safe to execute.\n")
        print(f"------ Go to {PYTHON_CODE_EXECUTER}\n")
        return Command(
                update={
                    "script_security_issues": None,
                    # update the message history
                    # "messages": [ToolMessage("Successfully looked up user information", tool_call_id=tool_call_id)]
                },
                goto=PYTHON_CODE_EXECUTER
            )
    else:
        if Python_script_check >= max_Python_script_check:
            print(f"-------- Go to {END}\n")
            return Command(
                goto=END
            )
              
        Python_script_check = Python_script_check + 1
        # state.update({
        #     "script_security_issues": response.reason,
        #     "Python_script_check": Python_script_check
        # })
        
        print(f"-------- Security Issues Found ({Python_script_check}): {response.reason}\n")
        print(f"-------- Go to {PYTHON_CODE_RE_GENERATION}\n")
        return Command(
            update={
                "script_security_issues": response.reason,
                "Python_script_check": Python_script_check
            },
            goto=PYTHON_CODE_RE_GENERATION
        )
         
    