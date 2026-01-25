from typing import Literal
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.utils import print_text
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from langgraph.constants import END
from receptionist_ai.tools_function import (
    get_all_events,
    busy_times,
    total_avaliability,
    make_meeting,
    get_current_time,
    get_day_from_date,
)
from receptionist_ai.agent_state import MessagesState

load_dotenv()

MY_ENV_VAR = os.getenv("CHATGPT_TOKEN")

tools = [make_meeting, get_current_time, get_day_from_date]
tools_by_name = {tool.name: tool for tool in tools}

llm = ChatOpenAI(
    model="gpt-4.1-mini", stream_usage=True, api_key=MY_ENV_VAR
).bind_tools(tools)


def initiliaser():
    """Calls the API's required for the receptionist to know which times and types of meeting they can offer"""
    events = get_all_events()
    busy = busy_times()
    availability = total_avaliability()

    return f"Receptionist Context:\nMeeting Types: {events}\nBusy Times: {busy}\nAvailability: {availability}"


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    messages = state.get("messages")

    # Call the LLM with current messages
    response = llm.invoke(messages)

    # ONLY return the new message in a list
    # The reducer (operator.add) will append this to the state automatically
    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        print(observation)
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        print(result)
    return {"messages": result}
