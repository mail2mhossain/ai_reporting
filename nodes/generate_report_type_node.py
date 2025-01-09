import json
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Command
from langchain_openai import ChatOpenAI
from decouple import config
from nodes.agent_state import AgentState
from nodes.nodes_name import PYTHON_CODE_GENERATOR


sys_msg = """
    You are a skilled data formatter and visualization expert. Combine numerical analysis with narrative descriptions, visualizations and charts.
    Given a DuckDB SQL query and the resulting data from the query, your task is to transform the output into a visually appealing HTML format.
    
    Here’s what you need to do:
    1. **Analyze the result data**: Review the structure of the result and determine the best way to present it, whether in a table, bar chart, line chart, or pie chart.
    2. **Charts**: You may use only 'bar', 'line', 'pie', 'scatter', or 'heatmap' charts for visualizing the data. Choose a chart type based on the data distribution and what best represents the information.
        - Provide the chart details in the following format:
            ```json
            {
                'format': 'chart',
                'chart_type': '<A suitable chart format.',
                'chart_title': '<A suitable title for the chart>',
            }
            ```
        - Example: 
            ```json
            {
                'format': 'chart',
                'chart_type': 'bar',
                'chart_title': 'Monthly Sales Data',
            }
            ```
    3. **Tables**: If a chart is not suitable for the data, present it in table format:
        - Provide the table details in this format:
            ```json
            {
                'format': 'table',
                'headers': <list of column headers>,
                'rows': <list of rows with corresponding data>
            }
            ```
        - Example:
            ```json
            {
                'format': 'table',
                'headers': ['Name', 'Age', 'City'],
                'rows': [
                    ['John', 28, 'New York'],
                    ['Jane', 22, 'Los Angeles'],
                    ['Doe', 35, 'Chicago']
                ]
            }
            ```
    4. **No Visual Needed**: If the data doesn't require a chart or table (e.g., simple text), respond with a plain message in the following format:
        ```json
        {
            'format': 'message',
            'content': 'Provide the text message here'
        }
        ```
    Your goal is to select the most appropriate visual (chart, table, or message) based on the query results and format the response as structured JSON.
"""

def get_report_type(state: AgentState) -> AgentState:
    print("--- DEFINE REPORT TYPE ---")
    
    OPENAI_API_KEY = config("OPENAI_API_KEY")

    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-2024-08-06", temperature=0, max_tokens=16000, model_kwargs={"response_format": { "type": "json_object" }})

    sql_query = state["SQL_query"]
    data = state["data_frame"]
    # print(f"Data: {data}\n")

    prompt = [
        SystemMessage(content=sys_msg),
        HumanMessage(content=f"""query: {sql_query}, result: {str(data)}""")
    ]

    response = llm.invoke(prompt)

    # print(f"Report Type: {response.content}")

    return Command(
        update={
            "report_type": response.content,
        },
        goto=PYTHON_CODE_GENERATOR
    ) 