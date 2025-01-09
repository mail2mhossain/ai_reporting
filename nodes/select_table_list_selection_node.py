import base64
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from decouple import config
from nodes.agent_state import AgentState
from nodes.nodes_name import QUERY_GENERATION


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    


def select_table_list(state: AgentState) -> AgentState:
    print("--- SELECT TABLE LIST ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    query = state["query"]
    erd_file = state['db_info']["erd_path"]
    image_data = encode_image(erd_file)

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    user_prompt = f"""
        The user has provided the following query: {query}. 
        Query is relevant to the ERD diagram. 
        Provide a comma-separated list of potential table names from the ERD that may be necessary to answer this query.
    """
    message = HumanMessage(
        content=[
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )

    llm = llm | StrOutputParser()
    selected_tables = llm.invoke([message])

    return Command(
        update={
            "selected_tables": selected_tables,
        },
        goto=QUERY_GENERATION
    ) 
