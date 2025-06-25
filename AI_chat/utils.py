import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.chains import RetrievalQA
from supabase import create_client
from duckduckgo_search import DDGS
import requests

# تحميل متغيرات البيئة
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# إعداد Supabase
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Embedding Model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Vector Store
vectorstore = SupabaseVectorStore(
    client=supabase_client,
    embedding=embedding_model,
    table_name="documents",
    query_name="match_documents"
)

def hf_inference_api(prompt):
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HUGGINGFACEHUB_API_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"temperature": 0.5, "max_new_tokens": 300}}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    if isinstance(result, list) and result:
        return result[0].get("generated_text", "")
    elif isinstance(result, dict) and "error" in result:
        return f"[HF API Error] {result['error']}"
    return str(result)

# Custom RAG answer function

def is_medical_question(question):
    medical_keywords = [
        "medicine", "drug", "treatment", "disease", "symptom", "pharmacy", "doctor", "hospital", "health", "tablet", "capsule", "side effect", "dose", "prescription", "medical", "illness", "pain", "infection", "antibiotic", "paracetamol", "ibuprofen", "acetaminophen", "aspirin", "diabetes", "hypertension", "cancer", "virus", "bacteria", "vaccine", "allergy", "pharmacist", "clinic", "surgery", "operation", "diagnosis", "therapy", "prescribe", "pharmaceutical"
    ]
    q = question.lower()
    return any(word in q for word in medical_keywords)

def answer_question(question):
    # Only allow medical questions
    if not is_medical_question(question):
        return "❌ This assistant only answers medical-related questions. Please ask a medical or drug-related question."
    # Retrieve context from vectorstore
    docs = vectorstore.similarity_search(question, k=3)
    if docs:
        context = "\n".join([doc.page_content for doc in docs])
        prompt = f"You are a helpful medical assistant. Only answer medical questions.\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        answer = hf_inference_api(prompt)
        if answer and "I don't know" not in answer:
            return answer
    # If no docs or no good answer, fallback to web search
    web_result = web_search_fallback(question)
    return f"from web:\n{web_result}"

# دالة البحث الاحتياطي عبر DuckDuckGo
def web_search_fallback(query):
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=1)]
        return results[0]['body'] if results else "No information found."
