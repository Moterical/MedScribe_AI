import os
from typing import TypedDict, Annotated, Sequence, Dict, Any, List
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.config import settings
from app.tools import (
    LogInteractionInput,
    EditInteractionInput,
    GenerateStudyPdfInput,
    GenerateFollowupEmailInput,
    ScheduleCalendarEventInput,
    SchedulingCalendarEventInput,
    execute_tool_action
)

# Define the State of our Graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    form_data: dict
    output_text: str

# Instantiate the LLM
# We primary target gemma2-9b-it, but if it has any tool calling issues, llama-3.3-70b-versatile is a robust fallback.
llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile", # Swapped gemma2-9b-it due to decommissioning
    temperature=0.1
)

# Bind the tools to the model
tools = [
    LogInteractionInput,
    EditInteractionInput,
    GenerateStudyPdfInput,
    GenerateFollowupEmailInput,
    ScheduleCalendarEventInput,
    SchedulingCalendarEventInput
]

# Create tool mappings for execution
tool_name_map = {
    "LogInteractionInput": "log_interaction",
    "EditInteractionInput": "edit_interaction",
    "GenerateStudyPdfInput": "generate_study_pdf",
    "GenerateFollowupEmailInput": "generate_followup_email",
    "ScheduleCalendarEventInput": "schedule_calendar_event",
    "SchedulingCalendarEventInput": "schedule_calendar_event"
}

llm_with_tools = llm.bind_tools(tools)

# Define the Agent System Prompt
SYSTEM_PROMPT = """You are an AI CRM assistant for pharmaceutical and medical device field representatives logging HCP (Healthcare Professional) interactions.
The Interaction Details Form fields on the left pane of the screen are completely DISABLED for manual interaction. The ONLY way to populate, modify, or update the form is through you calling tools.

You have the following tools available:
1. LogInteractionInput (log_interaction): Use this to extract and set all form fields when the user summarizes a meeting or interaction.
2. EditInteractionInput (edit_interaction): Use this when the user requests a correction to a specific field (e.g. "Actually the doctor was Dr. Watson, not Dr. Smith", "Change sentiment to Neutral", "Modify topics discussed to X").
3. GenerateStudyPdfInput (generate_study_pdf): Use this to create a dynamic clinical briefing PDF summarizing the trial data for the topics discussed. Trigger it whenever a study paper, clinical trial data, or brochure sharing is mentioned or requested.
4. GenerateFollowupEmailInput (generate_followup_email): Use this when the user requests a follow-up email draft or wants to mock send an email.
5. ScheduleCalendarEventInput (schedule_calendar_event): Use this to schedule follow-up meetings at a specific date and time.

Guidelines:
- Actively parse natural language statements.
- If a user mentions products discussed, samples distributed, or brochures shared, make sure to extract them and call the log_interaction tool.
- Differentiate clearly between drafting a follow-up email and scheduling a follow-up meeting. Do NOT call schedule_calendar_event when the user only asks to write, draft, or generate an email. Only call schedule_calendar_event when a future follow-up date/time/meeting is explicitly requested to be scheduled.
- Differentiate between inventory counts (e.g. products inside a bag/kit) and actual distributed items (e.g. handed out). Only log the quantity of distributed items, and ensure the sample_name is strictly the product/therapeutic area name (e.g. 'Diabetes-1 Sample'). Do not include any descriptive phrases like 'given to the doctor' or 'remaining in the bag' in the sample_name. If a quantity is shared but the product name is not explicitly repeated, attribute it to the active topic discussed.
- Initialize the form with current values. If the user tells you to update a field, call the edit_interaction tool.
- Be polite, professional, and focus on life science representative scenarios (compliance, medical studies, patient safety).
- After executing a tool, summarize what you have updated on the form in your reply to the user.
"""

def call_model(state: AgentState):
    """
    LLM caller node.
    """
    messages = state["messages"]
    # Prepend the system message
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    combined_messages = [system_msg] + list(messages)
    
    response = llm_with_tools.invoke(combined_messages)
    return {"messages": [response], "output_text": response.content}

def should_continue(state: AgentState):
    """
    Routing edge. Determines whether to execute tools or end the conversation step.
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "execute_tools"
    return END

def execute_tools_node(state: AgentState):
    """
    Tool execution node. Resolves tool calls, runs execute_tool_action, and appends ToolMessages.
    """
    last_message = state["messages"][-1]
    form_data = state["form_data"]
    
    tool_messages = []
    updated_form = form_data.copy()
    
    for tool_call in last_message.tool_calls:
        # Determine internal tool name from class name
        raw_name = tool_call["name"]
        internal_name = tool_name_map.get(raw_name, raw_name)
        
        args = tool_call["args"]
        print(f"DEBUG TOOL CALL: tool={internal_name}, args={args}")
        
        # Execute tool
        updated_form, result_str = execute_tool_action(internal_name, args, updated_form)
        
        tool_messages.append(
            ToolMessage(
                content=result_str,
                tool_call_id=tool_call["id"],
                name=raw_name
            )
        )
        
    return {
        "messages": tool_messages,
        "form_data": updated_form
    }

# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", call_model)
workflow.add_node("execute_tools", execute_tools_node)

# Set Entry Point
workflow.set_entry_point("agent")

# Add Conditional Edges
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "execute_tools": "execute_tools",
        END: END
    }
)

# Add normal edge back to agent
workflow.add_edge("execute_tools", "agent")

# Compile the Graph
agent_app = workflow.compile()

async def run_agent_workflow(message: str, history: List[Dict[str, str]], current_form: dict) -> tuple[str, dict]:
    """
    Drives the compiled LangGraph execution.
    Converts message history list into LangChain BaseMessage objects, executes the graph,
    and returns (assistant_response, updated_form_data).
    """
    # Build initial message chain
    messages = []
    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        elif h["role"] == "assistant":
            messages.append(AIMessage(content=h["content"]))
            
    # Append the new message
    messages.append(HumanMessage(content=message))
    
    # Run graph
    inputs = {
        "messages": messages,
        "form_data": current_form,
        "output_text": ""
    }
    
    config = {"configurable": {"thread_id": "hcp_session"}}
    result = await agent_app.ainvoke(inputs, config)
    
    # Extract final text and form
    output_text = result["output_text"]
    if not output_text and result["messages"]:
        # Fallback if final agent message is empty but has messages
        output_text = result["messages"][-1].content
        
    return output_text, result["form_data"]
