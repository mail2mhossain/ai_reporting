from langchain.prompts.chat import ChatPromptTemplate
from nodes.agent_state import AgentState
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain.schema import StrOutputParser
from decouple import config
from nodes.nodes_name import SANITIZE_SQL_QUERY, EXECUTE_SQL_QUERY


def get_schema(db_info, selected_tables):
    tables = db_info["details"]
    selected_info = [table for table in tables if table["table_name"] in selected_tables]
    return selected_info


sys_msg = """
    You are an expert SQL query generator with deep knowledge of PostgreSQL syntax and best practices. 
    You are given a PostgreSQL database schema which contains relevant tables, columns, and sample data, referred to as `relevant_tables_columns_sample_data`. 
    Additionally, you will receive a natural language user query, referred to as `query`, that needs to be transformed into a valid, efficient, 
    and correct PostgreSQL query. 

    Your task is to:
    1. Analyze the given 'domain_specific_terms' and `relevant_tables_and_columns` structure to identify the appropriate tables and columns needed for the query.
    2. Interpret the user's query and map it to the correct SQL operations (e.g., SELECT, JOIN, WHERE, GROUP BY, etc.).
    3. Ensure that the SQL query is optimized, adheres to PostgreSQL standards, and accurately represents the intent of the user's query.
    4. Handle edge cases such as ambiguous column names, missing conditions, or complex queries by making reasonable assumptions or asking for clarification when needed.
    5. DO NOT INCLUDE ```sql``` TAGS IN YOUR RESPONSE.
    Your response should consist solely of the generated SQL query in correct syntax, without any additional explanation.
"""

def generate_sql_query(state:AgentState)->AgentState:
    print("--- GENERATE SQL QUERY ---")
    
    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)

    prompt = ChatPromptTemplate(
        [
            ("system", sys_msg),
            ("human", """
                relevant_tables_and_columns: {relevant_tables_and_columns}
                query: {query}
            """)
        ]
    )

    relevant_tables_and_columns = get_schema(state["db_info"], state["selected_tables"])

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "relevant_tables_and_columns": relevant_tables_and_columns, 
        "query": state["rephrased_query"]
    })
    print(f"Generated SQL query: {response}")
    return Command(
        update={
            "SQL_query": response
        },
        goto=SANITIZE_SQL_QUERY
    ) 