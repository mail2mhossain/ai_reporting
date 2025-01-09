import base64
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from decouple import config
from nodes.agent_state import AgentState
from nodes.nodes_name import TABLE_SELECTION


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    


def re_write_query(state: AgentState) -> AgentState:
    print("--- RE-WRITING QUERY ---")

    OPENAI_API_KEY = config("OPENAI_API_KEY")
    GPT_MODEL = config("GPT_MODEL")

    query = state["query"]
    erd_file = state['db_info']["erd_path"]
    image_data = encode_image(erd_file)

    llm = ChatOpenAI(model_name=GPT_MODEL, temperature=0, openai_api_key=OPENAI_API_KEY)
    REPHRASED_QUERY_PROMPT = f"""
        The user has provided the following query: {query}. 
        The query is relevant to the ERD diagram. 
        Rewrite the query to make it align with the structure and relationships defined in the ERD diagram. 
        Ensure the rewritten query is concise, uses plain English, and matches the data's context. 
        Provide only the rewritten query.
    """
    message = HumanMessage(
        content=[
            {"type": "text", "text": REPHRASED_QUERY_PROMPT},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )

    llm = llm | StrOutputParser()
    rephrased_question = llm.invoke([message])

    print(f"Rephrased Query: {rephrased_question}")
    return Command(
        update={
            "rephrased_query": rephrased_question,
        },
        goto=TABLE_SELECTION
    ) 