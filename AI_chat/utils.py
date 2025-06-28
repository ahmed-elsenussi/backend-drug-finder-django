import os
import requests
from dotenv import load_dotenv
from django.apps import apps
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Supabase setup
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Vector store
vectorstore = SupabaseVectorStore(
    client=supabase_client,
    embedding=embedding_model,
    table_name="documents",
    query_name="match_documents"
)

# Search medicines
def fuzzy_search_medicine(question: str):
    Medicine = apps.get_model('inventory', 'Medicine')
    matches = Medicine.objects.annotate(
        sim_brand=TrigramSimilarity('brand_name', question),
        sim_generic=TrigramSimilarity('generic_name', question),
        sim_chemical=TrigramSimilarity('chemical_name', question),
    ).filter(
        Q(sim_brand__gt=0.3) |
        Q(sim_generic__gt=0.3) |
        Q(sim_chemical__gt=0.3)
    ).order_by('-sim_brand', '-sim_generic', '-sim_chemical')

    if matches.exists():
        context = []
        for med in matches:
            store = getattr(med, "store", None)
            store_name = getattr(store, "store_name", "Not specified")
            store_address = getattr(store, "store_address", "Not specified")
            context.append(
                f"{med.brand_name} ({med.generic_name}, {med.chemical_name}): {med.description}\n"
                f" Available at: {store_name} - {store_address}"
            )
        return "\n\n".join(context)
    return None

# Search pharmacies
def fuzzy_search_store(query: str):
    MedicalStore = apps.get_model('medical_stores', 'MedicalStore')
    matches = MedicalStore.objects.annotate(
        sim_name=TrigramSimilarity('store_name', query),
        sim_address=TrigramSimilarity('store_address', query),
        sim_desc=TrigramSimilarity('description', query),
    ).filter(
        Q(sim_name__gt=0.3) |
        Q(sim_address__gt=0.3) |
        Q(sim_desc__gt=0.3)
    ).order_by('-sim_name', '-sim_address', '-sim_desc')

    if matches.exists():
        context = []
        for store in matches:
            context.append(
                f"{store.store_name} ({store.store_type})\n Address: {store.store_address or 'Not provided'}\n Description: {store.description or 'N/A'}"
            )
        return "\n\n".join(context)
    return None

# HF model call
def call_hf_model(prompt: str):
    api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACEHUB_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.5
        }
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result[0].get("generated_text", "").strip() if isinstance(result, list) else str(result)
    except requests.exceptions.RequestException as e:
        return f"[Error calling HF API] {str(e)}"

# Main QA logic
def answer_question(question: str):
    # Step 1: Search medicine
    db_answer = fuzzy_search_medicine(question)
    if db_answer:
        return f"{db_answer}"

    # Step 2: Search pharmacy/store
    store_answer = fuzzy_search_store(question)
    if store_answer:
        return f"{store_answer}"

    # Step 3: Search documents
    docs = vectorstore.similarity_search(question, k=3)
    if docs:
        context = "\n\n".join([doc.page_content for doc in docs])
        prompt = f"Question: {question}\n\nContext:\n{context}\n\nAnswer:"
        answer = call_hf_model(prompt)
        if "i don't know" not in answer.lower():
            return f"{answer}"

    # Step 4: Nothing found
    return " Sorry, no relevant medical information found."
