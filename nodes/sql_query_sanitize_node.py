from typing_extensions import TypedDict, Literal
from langgraph.graph import END
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langgraph.types import Command
from nodes.agent_state import AgentState
from nodes.nodes_name import EXECUTE_SQL_QUERY, QUERY_GENERATION, RE_GENERATE_SQL_QUERY, SQL_QUERY_SANITIZE_REPORT
from langchain_openai import ChatOpenAI
from decouple import config

sys_msg = """
    You are an expert in SQL security. Your task is to analyze a given SQL query and determine whether it is a safe read-only query. 
    Only queries that retrieve data (i.e., SELECT queries) are allowed. 
    If the query contains any modifying operations like INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE, mark it as unsafe.
    Your response should be in the following format:
    
    {
        "is_safe": true/false,
        "reason": "<Explain why the query is safe or unsafe>"
    }
"""

class sanitizing_queries(BaseModel):
    is_safe: bool
    reason: str = Field(description="Reason for the safety status of the query")

def sanitize_sql_query(state:AgentState) -> Command[Literal[ EXECUTE_SQL_QUERY]]:
    """
    This function uses OpenAI's LLM to sanitize a given SQL query, allowing only 'SELECT' operations.
    Any query that contains 'UPDATE', 'INSERT', 'DELETE', or other modifying operations will be flagged as unsafe.

    Parameters:
    query (str): The SQL query to be sanitized.

    Returns:
    bool: True if the query is valid (SELECT-only), False otherwise.
    """
    print("--- SANITIZE SQL QUERY ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    
    sql_query = state["SQL_query"]
    # sanitize_check = state["sanitize_check"]
    # max_sanitize_check = state["max_sanitize_check"]
    
    # Define the system prompt to instruct the model to analyze the SQL query for safety
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=sys_msg),
            HumanMessage(content=f"""SQL query: {sql_query}""")
        ]
    )
    
    sanitize_chain = prompt | llm.with_structured_output(sanitizing_queries)
    
    response = sanitize_chain.invoke({"input":""})
    
    if response.is_safe == True:
        return Command(
            goto = EXECUTE_SQL_QUERY
        ) 
    else:
        return Command(
            update={
                "reports": response.reason
            },
        ) 