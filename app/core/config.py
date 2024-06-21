import os
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

# Redis cloud client setup
# redis_host = os.getenv("REDIS_HOST", "localhost")
# redis_port = int(os.getenv("REDIS_PORT", 6379))
# redis_client = Redis(host=redis_host, port=redis_port, db=0)

# Redis local client setup
redis_host = "localhost"
redis_port = 6379
redis_client = Redis(host=redis_host, port=redis_port, db=0)


BUCKET_NAME = os.getenv("BUCKET_NAME")
DATA_FOLDER = "data"
RESOURCE_FOLDER = "resources"
VECTOR_STORE_FOLDER = "vectorStore"

qa_system_template = """
You are a question answering bot. You have access to a database of documents and can provide answers to questions based on the information in the documents.
below context is provided for the user to get the best possible answer for the question.

Context : 
{context}

Just reply to the user without any formatting. Use above information as a reference to provide the best possible advice to the user.
Don't include chat history, question or context in the response. Refer the chat history to past conversation details.
"""

qa_human_template = """
chat history : 
{chat_history}

question :
{question}
"""

graph_system_template = """
You are a graph generating bot. You have access to the scenario as a text in context. You need to provide the 
mermaid graph notation as a text for the given scenario. User will provide the scenario then you need to get the best possible graph for the context.
Just reply to the user without any formatting. Use above information as a reference to provide the best possible graph representation for the user.

graph notation should be a text starting from graph TD and ending with a semicolon.

"""

graph_human_template = """
Scenario :
{Scenario}
"""

summary_system_template = """
You are a summarization bot. User will provide a paragraph and you need to summarize the paragraph in a few sentences.
All the important information should be included in the summary.
"""

summary_human_template = """
Paragraph :
{para}
"""

templates = {
    "qa": {
        "system": qa_system_template,
        "human": qa_human_template,
    },
    "graph": {
        "system": graph_system_template,
        "human": graph_human_template,
    },
    "summary": {
        "system": summary_system_template,
        "human": summary_human_template,
    }
}

