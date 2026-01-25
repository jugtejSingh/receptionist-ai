from langgraph.constants import START, END
from langgraph.graph import StateGraph
from agent_state import MessagesState
from nodes import llm_call, tool_node, should_continue, initiliaser
from prompts import SYSTEM_PROMPT

agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

from langchain.messages import HumanMessage

from langchain_core.messages import SystemMessage, HumanMessage

messages = [SystemMessage(content=str(SYSTEM_PROMPT))]

while True:
    user_input = input("You: ")

    if user_input.lower() in {"exit", "quit"}:
        print("Exiting chat.")
        break

    # Add user message to our local tracker
    messages.append(HumanMessage(content=user_input))

    # Invoke agent.
    # Note: result will contain the ENTIRE conversation history
    # because of how the graph is structured.
    result = agent.invoke({"messages": messages})

    # Update our local messages list to match the graph's updated state
    messages = result["messages"]

    # Get latest assistant message and print
    assistant_message = messages[-1]
    assistant_message.pretty_print()
