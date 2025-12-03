import os
from dotenv import load_dotenv

from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_google_gemini import ChatGoogleGenerativeAI
from langchain_google_gemini.embeddings import GoogleGenerativeAIEmbeddings

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")

# LLM + Embeddings
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=GEMINI_API_KEY
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GEMINI_API_KEY
)

# MongoDB Connection
client = MongoClient(MONGODB_URI)

DB_NAME = "test_db"
COLLECTION_NAME = "test_collection"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "test-index-1"

MONGODB_COLLECTION = client[DB_NAME][COLLECTION_NAME]

# Vector store
vector_store = MongoDBAtlasVectorSearch(
    collection=MONGODB_COLLECTION,
    embedding=embeddings,
    index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
    relevance_score_fn="cosine",
)

retriever = vector_store.as_retriever()

# ==============================
# SYSTEM PROMPT (IMPORTANT PART)
# ==============================
system_prompt = """
You are an AI assistant with access to retrieved knowledge documents.

Rules you must follow:

1. **Always base your answers on retrieved context first.**
2. If context is missing or unclear, acknowledge uncertainty instead of inventing unsupported facts.
3. When listing or explaining, be concise but meaningful.
4. If the user asks something outside provided documents, answer normally using general knowledge but mention that retrieval did not supply it.

Final output must be:
- **Helpful**
- **Truthful**
- **Direct**
"""

# Prompt setup
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# Chains
document_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retriever, document_chain)

# Invoke
ai_response = chain.invoke({"input": "Three facts about animals"})
print(ai_response["answer"])

client.close()
