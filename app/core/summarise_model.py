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

summary_template = templates["summary"]


def set_custom_prompt(difficulty: int):
    """
    Prompt template for QA retrieval for each vectorstore
    """

    if difficulty not in [1, 2, 3]:
        difficulty = 1

    system_template = summary_template[difficulty - 1]["system"]
    human_template = summary_template[difficulty - 1]["human"]

    system_message_template = SystemMessagePromptTemplate.from_template(system_template)
    human_message_template = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_template, human_message_template]
    )

    return chat_prompt


def load_llm():
    llm = ChatOpenAI(model="gpt-3.5-turbo", verbose=True)
    return llm


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


def final_result(query, difficulty, request: Request):
    prompt = set_custom_prompt(difficulty)
    chain = qa_bot(prompt)
    input_data = {"para": query}
    chain_response = chain.invoke(input_data, config={"callbacks": [CustomHandler()]})

    # debuggingLLM({"chat_history": chat_history, "question": query, "context": context, "response": chain_response})
    return chain_response
