import base64
from typing_extensions import TypedDict, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from decouple import config
from nodes.agent_state import AgentState
from nodes.nodes_name import RE_WRITE_QUERY, QUERY_RELEVANCY_REPORT

user_msg = """
        Evaluate the query: {query} based on the following:

        1. Alignment with the ERD diagram: Does the query match the structure and relationships defined in the ERD?  
        2. Safety: Is it a read-only query? Only data retrieval queries (e.g., SELECT) are allowed.  

        If the query includes any operations that modify the database, such as INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE, label it as unsafe.

        - Clearly explain why the query is unsafe in simple terms so the user understands the issue and knows how to fix it.  

        If the query does not align with the ERD, assign a "Relevance score" of no.  
        If the query is unsafe, also assign a "Relevance score" of no.

        - For queries that are either irrelevant to the ERD or unsafe, provide a plain and clear explanation to help the user identify and address the problem.
    """



def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def check_query_relevancy(state: AgentState) -> Command[Literal[ RE_WRITE_QUERY ]]:
    print("--- QUERY RELEVANCY CHECK ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    query = state["query"]
    db_info = state["db_info"]
    erd_file = db_info["erd_path"]

    
    class grade(BaseModel):
        """Binary score for relevance check."""
        binary_score: str = Field(description="Relevance score 'yes' or 'no'")
        reason: str = Field(description="Reason for the score")

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    llm_with_tool = llm.with_structured_output(grade)
    image_data = encode_image(erd_file)

    message = HumanMessage(
        content=[
            {"type": "text", "text": f"Does the query: {query} align with the structure and relationships defined in the ERD diagram?"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )

    scored_result = llm_with_tool.invoke([message])
    grade = scored_result.binary_score

    if grade == "yes":
        return Command(
            goto = RE_WRITE_QUERY
        ) 
    else:
        return Command(
            update={
                "reports": scored_result.reason
            },
        ) 

