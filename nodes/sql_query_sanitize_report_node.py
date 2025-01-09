from nodes.agent_state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
from decouple import config


sys_msg = """
    You are an expert in SQL security. Your task is to analyze a given SQL query and determine whether it is a safe read-only query. 
    Only queries that retrieve data (i.e., SELECT queries) are allowed. 
    If the query contains any modifying operations like INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE, mark it as unsafe.

    Explain why the sql query is unsafe in plain and simple English to make it clear and user-friendly, ensuring the user understands the problem and can take corrective action. 
"""


def sql_query_sanitize_report(state: AgentState) -> AgentState:
    print("--- SQL QUERY SANITIZE REPORT ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    sql_query = state["SQL_query"]

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=sys_msg),
            HumanMessage(content=f"""SQL query: {sql_query}""")
        ]
    )

    chain = prompt | llm | StrOutputParser()
    SQL_sanitizer_report = chain.invoke({"sql_query": sql_query})

    return {"reports": SQL_sanitizer_report}