from nodes.agent_state import AgentState
from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
from decouple import config

sys_msg = """
    The system encountered an error while executing the SQL query. The error message is as follows:
    SQL Execution Error: {SQL_error}
    Rewrite this error message in plain English to make it clear and user-friendly, ensuring the user understands the problem and can take corrective action. 
    Suggest possible solutions, such as checking the table name or verifying if the table exists in the database.
"""

def sql_query_error_report(state: AgentState) -> AgentState:
    print("--- SQL QUERY EXECUTION ERROR REPORT ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    SQL_error = state['SQL_error']

    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY, temperature=0, model=GPT_MODEL, streaming=False, cache=False)

    prompt = PromptTemplate(
        template=sys_msg,
        input_variables=["SQL_error"],
    )

    chain = prompt | model | StrOutputParser()
    SQL_error_report = chain.invoke({"SQL_error": SQL_error})
    
    return {
        "reports": SQL_error_report
    }