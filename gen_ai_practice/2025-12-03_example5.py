import os
from dotenv import load_dotenv

from pymongo import MongoClient

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from langchain_mongodb import MongoDBAtlasVectorSearch


# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

# LLM + embedding models
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=GEMINI_API_KEY
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GEMINI_API_KEY
)

# MongoDB setup
client = MongoClient(MONGO_URI)

DB_NAME = "test_db"
COLLECTION_NAME = "test_collection_pdf"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "test-index-pdf"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

# Vector store
vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine"
)

retriever = vector_store.as_retriever()


# System prompt
system_prompt = """
You are a retrieval-augmented assistant.
You must:
• Only answer using information from the retrieved documents.
• If the documents lack the answer, say you do not have enough information.
Be concise and factual.
"""

# Build chat chain
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

document_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retriever, document_chain)

# Example query
ai_response = chain.invoke({"input": "what is the genetic syndromes for diabetes"})
print(ai_response["answer"])

client.close()
