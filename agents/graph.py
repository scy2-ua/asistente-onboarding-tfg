import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.checkpoint.memory import MemorySaver

from agents.prompts import EXPLAINER_PROMPT, AUDITOR_PROMPT, CRITIC_PROMPT, HR_PROMPT, ROUTER_PROMPT
from core.document_processor import get_vectorstore

def init_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    def explainer_agent(state: MessagesState):
        user_message = state["messages"][-1].content
        docs = retriever.invoke(user_message)
        context_code = "\n\n".join(doc.page_content for doc in docs)
        reglas = st.session_state.get("reglas_corporativas", "No hay manuales cargados.")
        
        prompt = EXPLAINER_PROMPT.format(context_code=context_code, reglas=reglas)
        return {"messages": [llm.invoke([SystemMessage(content=prompt)] + state["messages"])]}

    def auditor_agent(state: MessagesState):
        user_message = state["messages"][-1].content
        docs = retriever.invoke(user_message)
        context_code = "\n\n".join(doc.page_content for doc in docs)
        reglas = st.session_state.get("reglas_corporativas", "")
        
        prompt = AUDITOR_PROMPT.format(reglas=reglas, context_code=context_code)
        return {"messages": [llm.invoke([SystemMessage(content=prompt)] + state["messages"])]}

    def critic_agent(state: MessagesState):
        reglas = st.session_state.get("reglas_corporativas", "")
        prompt = CRITIC_PROMPT.format(reglas=reglas)
        return {"messages": [llm.invoke([SystemMessage(content=prompt)] + state["messages"])]}

    def hr_agent(state: MessagesState):
        reglas = st.session_state.get("reglas_corporativas", "")
        prompt = HR_PROMPT.format(reglas=reglas)
        return {"messages": [llm.invoke([SystemMessage(content=prompt)] + state["messages"])]}

    # Nodo conversacional sin dependencias de Retrieval.
    def chat_agent(state: MessagesState):
        # Este agente utiliza exclusivamente el contexto en memoria (MessageHistory).
        system_prompt = "Eres el Mentor IA de TechCorp. Tu objetivo es conversar de forma natural y empática. Usa el historial de la conversación para recordar el nombre, rol y preferencias del usuario si te las ha dicho."
        return {"messages": [llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])]}

    def route_query(state: MessagesState):
        user_message = state["messages"][-1].content.lower()
        if any(keyword in user_message for keyword in ["audita", "revisa", "corrige", "refactoriza"]): 
            return "auditor"
        try:
            res = llm.invoke([SystemMessage(content=ROUTER_PROMPT), HumanMessage(content=user_message)]).content.strip().upper()
        except Exception:
            return "explainer"
            
        # Lógica de enrutado.
        if "RRHH" in res:
            return "hr"
        elif "CHARLA" in res:
            return "chat"
        else:
            return "explainer"

    workflow = StateGraph(MessagesState)
    workflow.add_node("explainer", explainer_agent)
    workflow.add_node("auditor", auditor_agent)
    workflow.add_node("critic", critic_agent)
    workflow.add_node("hr", hr_agent)
    workflow.add_node("chat", chat_agent) # Registrar nodo conversacional
    
    workflow.add_conditional_edges(START, route_query, {
        "auditor": "auditor", 
        "explainer": "explainer", 
        "hr": "hr",
        "chat": "chat" # Configurar ruta hacia nodo conversacional
    })
    
    workflow.add_edge("auditor", "critic")
    workflow.add_edge("critic", END)
    workflow.add_edge("explainer", END)
    workflow.add_edge("hr", END)
    workflow.add_edge("chat", END) # Flujo de término del nodo conversacional
    
    return workflow.compile(checkpointer=MemorySaver())