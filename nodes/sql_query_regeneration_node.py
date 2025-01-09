from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from decouple import config
from nodes.nodes_name import SANITIZE_SQL_QUERY
from .agent_state import AgentState


def get_schema(db_info, selected_tables):
    tables = db_info["details"]
    selected_info = [table for table in tables if table["table_name"] in selected_tables]
    return selected_info


SQL_QUERY_CHECKER = """
    Upon executing {sql_query} on the PostgreSQL database, the following SQL error referred to as 'SQL error' was encountered, delineated by triple backticks:

    ```
    {sql_error}
    ```
    You are given a PostgreSQL database schema which contains relevant tables and columns, referred to as `relevant_tables_and_columns`. 
    {db_schema}

    You are also provided domain knowledge, referred as 'domain_specific_terms':
    {domain_specific_terms} 

    Your task is to:
    1. Analyze the given `relevant_tables_and_columns`, 'domain_specific_terms' and 'SQL error' to identify the appropriate tables and columns needed for the query.
    2. Re-write the correct SQL operations (e.g., SELECT, JOIN, WHERE, GROUP BY, etc.).
    3. Ensure that the SQL query is optimized, adheres to PostgreSQL standards, and accurately represents the intent of the user's query.
    4. Handle edge cases such as ambiguous column names, missing conditions, or complex queries by making reasonable assumptions or asking for clarification when needed.
    5. DO NOT INCLUDE ```sql``` TAGS IN YOUR RESPONSE.
    
    Your response should consist solely of the generated SQL query in correct syntax, without any additional explanation.
    """

def regenerate_sql_query(state: AgentState) -> AgentState:
    print("--- RE-GENERATE SQL QUERY ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)

    sql_query = state['SQL_query']
    sql_error = state['SQL_error']
    relevant_tables_and_columns = get_schema(state["db_info"], state["selected_tables"])

    sql_generation_prompt = PromptTemplate(
        template=SQL_QUERY_CHECKER,
        input_variables=[
            "sql_query",
            "sql_error",
            "db_schema",
            "domain_specific_terms"
        ],
    )

    chain = sql_generation_prompt | llm | StrOutputParser()
    sql_query = chain.invoke(
        {
            "sql_query": sql_query,
            "sql_error": sql_error,
            "db_schema": relevant_tables_and_columns,
            "domain_specific_terms": ""
        }
    )
   
    return Command(
        update={
            "SQL_query": sql_query,
            "SQL_error": None,
            "sql_generation_try": state['sql_generation_try'] + 1
        },
        goto=SANITIZE_SQL_QUERY
    ) 