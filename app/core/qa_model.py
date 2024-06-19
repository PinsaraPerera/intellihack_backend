from fastapi import Request
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.llms import CTransformers
from .openAI_embeddings import load_vector_db
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pathlib import Path
import uuid

from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    ChatPromptTemplate,
)
from langchain.callbacks.base import BaseCallbackHandler
from logging_config import logger
from typing import Any, Dict, List
from app.core.config import templates

qa_template = templates["qa"]

system_template = qa_template["system"]
human_template = qa_template["human"]


def set_custom_prompt():
    """
    Prompt template for QA retrieval for each vectorstore
    """

    system_message_template = SystemMessagePromptTemplate.from_template(system_template)
    human_message_template = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_template, human_message_template]
    )

    return chat_prompt


def load_llm():
    llm = ChatOpenAI(model="gpt-3.5-turbo", verbose=True)
    return llm


def get_context_from_vector_db(query: str, request: Request, user_email: str):
    session_id = request.session.get('session_id')
    if not session_id:
        session_id = request.session['session_id'] = str(uuid.uuid4())
    db = load_vector_db(session_id, user_email)

    docs_with_scores = db.similarity_search_with_score(query, k=4)

    # Sort results by score (lower is better) and select top 2
    docs_with_scores.sort(key=lambda x: x[1])
    top_results = docs_with_scores[:2]

    if top_results:
        context = "\n".join(
            [result[0].page_content.replace("\n", " ") for result in top_results]
        )
        return context
    return ""


def debuggingLLM(data: dict):
    print("========debugging start==========\n\n")
    print(f"chat history: {data['chat_history']}\n\n")
    print(f"context: {data['context']}\n\n")
    print(f"question: {data['question']}\n\n")
    print(f"response: {data['response']}\n\n")


def llm_chain(llm, prompt):
    llm_chain = prompt | llm | StrOutputParser()
    return llm_chain


def qa_bot(prompt):
    llm = load_llm()
    chain = llm_chain(llm, prompt)
    return chain


class CustomHandler(BaseCallbackHandler):
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        formatted_prompts = "\n".join(prompts)
        logger.info(f"Prompt:\n{formatted_prompts}")


def final_result(query, chat_history, request: Request, user_email: str):
    context = get_context_from_vector_db(query, request, user_email)
    prompt = set_custom_prompt()
    chain = qa_bot(prompt)
    input_data = {"chat_history": chat_history, "question": query, "context": context}
    chain_response = chain.invoke(input_data, config={"callbacks": [CustomHandler()]})

    # debuggingLLM({"chat_history": chat_history, "question": query, "context": context, "response": chain_response})
    return chain_response
