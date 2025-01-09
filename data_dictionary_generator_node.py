import base64
import json
from langchain_core.messages import HumanMessage
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from decouple import config

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
class Column(BaseModel):
    """Column Details."""
    name: str = Field(description="Name of the column")
    description: str = Field(description="Detail description of the column")
    data_type: str = Field(description="Data type of the column")
    primary_key: Optional[str] = Field(description="Primary key of the column")
    foreign_key: Optional[str] = Field(description="Foreign key of the column")

class Table(BaseModel):
    """Table Details."""
    name: str = Field(description="Name of the table")
    description: str = Field(description="Detail description of the table")
    columns: list[Column]

class Database(BaseModel):
    """Database Description."""
    description: str = Field(description="Detail description of the column")
    tables: list[Table]


sys_msg = """
    You are export on pandas data frame.
"""

user_msg = """
    I have data frame {df_head}. 
    Please generate detail description of each column:
"""

def generate_data_dictionary(erd_path) :
    print("--- GENERATE DATA DICTIONARY ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    IMAGE_PATH = "images\\ERD_of_Chinook_Database_origin.png"


    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    structured_llm = llm.with_structured_output(Database)
    image_data = encode_image(IMAGE_PATH)

    message = HumanMessage(
        content=[
            {"type": "text", "text": "Based on attached ERD diagram, Generate Data Dictionary"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )
    structured_llm = llm.with_structured_output(Database)
    database = structured_llm.invoke([message])
    
    return database


# data_dictionary = generate_data_dictionary("")
# print(f"Data Type: {type(data_dictionary)}")
# data_dictionary = data_dictionary.model_dump() 
# data_dictionary["db_name"]="Chinook_test"
# data_dictionary["connection_string"]= "Database Connection String"
# data_dictionary["erd_path"]= "images\\ERD_of_Chinook_Database_origin.png"

# print(f"Data Dictionary: {data_dictionary}")