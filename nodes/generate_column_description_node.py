import pandas as pd
import duckdb 
from langchain_experimental.tools.python.tool import PythonAstREPLTool, PythonREPLTool
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from typing import Optional
from pydantic import BaseModel, Field
from langchain.schema import StrOutputParser
from langchain_openai import ChatOpenAI
from nodes.db_state import DBState
from decouple import config


class ColumnDescription(BaseModel):
    """Column Description."""

    name: str = Field(description="Name of the column")
    description: str = Field(description="Detail description of the column")
 
class ColumnList(BaseModel):
    columns: list[ColumnDescription]


sys_msg = """
    You are export on pandas data frame.
"""

user_msg = """
    I have data frame {df_head}. 
    Please generate detail description of each column:
"""

def generate_column_description(state: DBState) -> DBState:
    print("--- GENERATE COLUMN DESCRIPTION ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    df = state["data_frame"]

    df_head = str(df.head(5).to_markdown()) 

    prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(sys_msg),
                HumanMessagePromptTemplate.from_template(user_msg),
            ]
        )
    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    structured_llm = llm.with_structured_output(ColumnList)
    chain = prompt | structured_llm

    column_description = chain.invoke({"df_head": df_head}) 

    # Convert to JSON
    column_description_json = column_description.model_dump_json(indent=4)
    
    return {
        "column_descriptions": column_description_json,
    }

# parquet_file_path = "../data/green_tripdata_2024-01.parquet"
# conn_in_memory = duckdb.connect(':memory:')
# conn_in_memory.sql(f"CREATE TABLE green_trip_data AS SELECT * FROM read_parquet('{parquet_file_path}');")
# df = conn_in_memory.execute('''  
#     SELECT 
#         *
#     FROM
#     green_trip_data
#     Limit 5
#     ''').df()

# conn_in_memory.close()
# results = generate_column_description({"dataframe":df})
# column_description = results['column_description']

# # column_description_json = column_description.model_dump_json(indent=4)
# print("Serialized JSON:\n", column_description)

# # Load back from JSON
# loaded_column_description = ColumnList.model_validate_json(column_description)
# print("\nDeserialized ColumnList Object:\n", loaded_column_description)
