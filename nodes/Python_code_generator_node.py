import json
import pandas as pd
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
from decouple import config
from langgraph.types import Command
from nodes.nodes_name import SANITIZE_PYTHON_SCRIPT
from nodes.agent_state import AgentState


def get_schema(db_info, selected_tables):
    tables = db_info["details"]
    selected_info = [table for table in tables if table["table_name"] in selected_tables]
    return selected_info

sys_msg = """
        1. Based on user query, SQL query is:
        {SQL_query} 
        2. SQL query execution result is:
        {execution_results}
        3. Based on above SQL query and execution results, report type should be
        {report_type}
        4. DO NOT USE ENUM OR NUMERIC REPRESENTATION OF A COLUMN REPORTS, ALWAYS USE COLUMN DESCRIPTION. Column Descriptions: {column_descriptions}. 
        5. When creating the script, think about security, unauthorized access, resource usage, and avoiding any unnecessary external network connections.
        6. Respond with only the Python script in the correct syntax, without adding explanations.
        7. Generate a single output results as string based on above Report Type and Execution Results and Print the output results using `print(...)`
    """

def generate_Python_code(state: AgentState):
    print("--- PYTHON CODE GENERATOR ---")
    
    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    rephrased_query = state["rephrased_query"]
    db_schema = get_schema(state["db_info"], state["selected_tables"])
    SQL_query = state["SQL_query"]
    report_type= state["report_type"]
    df = state["data_frame"]

    rephrased_query = f"""
        {rephrased_query}
        Do it in Python and generate a single report. Report should include text, tables, charts, images and plots.
        Combine numerical analysis with narrative descriptions, visualizations and charts.
        If any visualization is needed, save it in images folder with unique file name including uuid.
        Include the saved image with its RELATIVE PATH in the reports as markdown. 
        Generate the reports in markdown format (DO NOT INCLUDE ```markdown) and print the markdown reports.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(sys_msg),
            HumanMessagePromptTemplate.from_template(rephrased_query),
        ]
    )

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)

    chain = prompt | llm | StrOutputParser()
    
    code = chain.invoke({"SQL_query": SQL_query, 
                         "column_descriptions": str(db_schema),
                         "execution_results": str(df),
                         "report_type": report_type})

    print(f"Python Code:\n{code}")
    return Command(
        update={
            "Python_Code" : code,
            "execution_error": None,
        },
        goto = SANITIZE_PYTHON_SCRIPT
    )