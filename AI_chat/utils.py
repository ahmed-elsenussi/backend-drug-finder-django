import os
import re
import requests
from dotenv import load_dotenv
from django.apps import apps
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from typing import List
from langchain.chains import RetrievalQA
from langchain.llms.base import LLM
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase import create_client

# Track last medicine and shown stores
last_medicine_asked = None
shown_stores = set()

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

# Custom HuggingFace API wrapper
class CustomHFLLM(LLM):
    def _call(self, prompt: str, stop: List[str] = None) -> str:
        response = requests.post(
            "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
            headers={
                "Authorization": f"Bearer {HUGGINGFACEHUB_API_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": prompt,
                "parameters": {
                    "temperature": 0.5,
                    "max_new_tokens": 300,
                },
            },
        )
        result = response.json()
        if isinstance(result, list):
            return result[0].get("generated_text", "").strip()
        return str(result)

    @property
    def _llm_type(self) -> str:
        return "custom_hf_api"

# LLM + Retriever + RAG Chain
llm = CustomHFLLM()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

def fuzzy_search_medicine(query: str):
    global last_medicine_asked, shown_stores

    Medicine = apps.get_model('inventory', 'Medicine')
    query_lower = query.lower()
    ask_for_places = any(kw in query_lower for kw in ["where", "location", "available", "which pharmacy", "contain", "have", "stock"])

    matches = Medicine.objects.annotate(
        sim_brand=TrigramSimilarity('brand_name', query),
        sim_generic=TrigramSimilarity('generic_name', query),
        sim_chemical=TrigramSimilarity('chemical_name', query),
    ).filter(
        Q(sim_brand__gt=0.3) |
        Q(sim_generic__gt=0.3) |
        Q(sim_chemical__gt=0.3)
    ).order_by('-sim_brand', '-sim_generic', '-sim_chemical')

    if not matches.exists():
        return None

    seen = set()
    med_results = []
    pharmacy_results = []
    found_new_store = False

    for med in matches:
        store = getattr(med, "store", None)
        store_name = getattr(store, "store_name", "Not specified")
        store_address = getattr(store, "store_address", "Not specified")

        key = (med.brand_name.lower(), store_name.lower())
        if key in seen:
            continue
        seen.add(key)

        brand = (med.brand_name or "").strip()
        generic = (med.generic_name or "").strip()
        chemical = (med.chemical_name or "").strip()
        description = (med.description or "No description available").strip()

        last_medicine_asked = brand.lower()

        name_parts = list({name for name in [generic, chemical] if name and name.lower() != brand.lower()})
        name_str = ", ".join(name_parts)

        description = re.sub(r'\b(\w+)(\s+\1\b)+', r'\1', description, flags=re.IGNORECASE)
        description = re.sub(r'([a-zA-Z]+)\1{1,}', r'\1', description)

        if ask_for_places:
            store_key = f"{store_name} - {store_address}"
            if store_key in shown_stores:
                continue
            shown_stores.add(store_key)
            pharmacy_results.append(f"{store_name} - {store_address}")
            found_new_store = True
            break
        else:
            if name_str:
                med_results.append(f"{brand} ({name_str}): {description}\nWould you like to know where to find it?")
            else:
                med_results.append(f"{brand}: {description}\nWould you like to know where to find it?")

    if ask_for_places:
        if not found_new_store:
            return "❌ There are no more pharmacies that stock this medicine."
        return "\n\n".join(pharmacy_results)

    return "\n\n".join(med_results)

def fuzzy_search_store(query: str):
    global shown_stores

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

    context = []
    for store in matches:
        store_key = f"{store.store_name} - {store.store_address}"
        if store_key in shown_stores:
            continue
        shown_stores.add(store_key)
        context.append(
            f"{store.store_name} ({store.store_type})\nAddress: {store.store_address or 'Not provided'}\nDescription: {store.description or 'N/A'}"
        )
        break

    if context:
        return "\n\n".join(context)
    return None

def rag_answer_question(question: str):
    result = qa_chain.invoke({"query": question})
    answer = result.get("result", "")
    sources = result.get("source_documents", [])
    return answer, sources

def is_medical_question(question: str) -> bool:
    medical_keywords = [
        "medicine", "drug", "pharmacy", "pharmacist", "dose", "treatment", "prescription",
        "symptom", "disease", "illness", "diabetes", "infection", "antibiotic", "blood pressure",
        "insulin", "amoxicillin", "metformin", "side effect", "interaction", "pill", "tablet",
        "capsule", "health", "allergy", "asthma", "pain", "cancer", "renal", "liver", "cardio",
        "glucose", "hypertension", "fever", "cold", "flu", "eczema", "rash", "nausea", "vomiting"
    ]
    question = question.lower()
    return any(re.search(rf"\b{kw}\b", question) for kw in medical_keywords)

def detect_intent(question: str) -> str:
    q = question.lower().strip()

    greetings = ["hi", "hello", "hey", "good morning", "good evening", "how are you", "yo"]
    thankyou = ["thank you", "thanks", "appreciate it", "got it", "okay", "ok", "great", "cool", "awesome", "fine"]
    ask_keywords = [
        "i want to ask", "i have a question", "can i ask", "may i ask", "ask you", "question about",
        "what is", "who is", "tell me", "define", "meaning of"
    ]
    project_keywords = [
        "project", "system", "how it works", "how does it work", "who built", "tech stack",
        "features", "architecture", "backend", "frontend", "tools used", "workflow"
    ]

    if any(g in q for g in greetings):
        return "greeting"
    if any(t in q for t in thankyou):
        return "thankyou"
    if any(p in q for p in project_keywords):
        return "project_info"
    if any(k in q for k in ask_keywords):
        return "ask_medicine_info"

    med_keywords = ["medicine", "drug", "pill", "tablet", "capsule", "treatment", "dose", "prescription"]
    store_keywords = ["pharmacy", "store", "location", "available", "stock", "where"]

    if any(med_kw in q for med_kw in med_keywords):
        return "ask_medicine_info"
    if any(store_kw in q for store_kw in store_keywords):
        return "ask_pharmacy_location"

    return "fallback"

def answer_question(question: str):
    global last_medicine_asked, shown_stores

    question_lower = question.strip().lower()
    print("Thinking...")

    intent = detect_intent(question_lower)

    if intent == "greeting":
        return "👋 Hello! How can I assist you today? You can ask me about any medicine, pharmacy, or health-related topic."

    if intent == "thankyou":
        return "😊 You're welcome! Let me know if you have another question."

    # ✅ NEW: Handle follow-up confirmations like "yes"
    if question_lower in ["yes", "yeah", "yep", "sure", "ok", "okay", "please", "please do", "go ahead", "where", "tell me where"]:
        if last_medicine_asked:
            return fuzzy_search_medicine(f"where to find {last_medicine_asked}")
        else:
            return "❓ I need to know which medicine you're referring to. Could you mention its name?"

    if intent == "ask_medicine_info":
        shown_stores.clear()
        med_info = fuzzy_search_medicine(question)
        if med_info:
            return f"🧪 Info:\n\n{med_info}"

        if is_medical_question(question) and len(question.split()) > 4:
            try:
                answer, sources = rag_answer_question(question)
                if "i don't know" in answer.lower():
                    return "🤔 Sorry, I couldn't find enough information to answer that."
                source_texts = "\n\n".join([doc.page_content for doc in sources])
                return f"💡 Answer:\n\n{answer}\n\n📄 [Source Documents]:\n{source_texts}"
            except Exception:
                return "❌ An error occurred while processing the medical answer. Please try again later."

        return "❌ Sorry, I couldn't find information on that medicine."

    if intent == "ask_pharmacy_location":
        if last_medicine_asked:
            return fuzzy_search_medicine(f"where to find {last_medicine_asked}")

        store_info = fuzzy_search_store(question)
        if store_info:
            return f"🏥 Pharmacy Info:\n\n{store_info}"

        return "❌ Sorry, I couldn't find any pharmacies matching your query."

    if intent == "project_info":
        try:
            answer, sources = rag_answer_question(question)
            if "i don't know" in answer.lower():
                return "🤔 Sorry, I couldn't find enough information about the project."
            source_texts = "\n\n".join([doc.page_content for doc in sources])
            return f"📘 Project Info:\n\n{answer}\n\n📄 [Source Snippets]:\n{source_texts}"
        except Exception:
            return "❌ Error retrieving project information."

    if is_medical_question(question) and len(question.split()) > 4:
        try:
            answer, sources = rag_answer_question(question)
            if "i don't know" in answer.lower():
                return "🤔 Sorry, I couldn't find enough information to answer that."
            source_texts = "\n\n".join([doc.page_content for doc in sources])
            return f"💡 Answer:\n\n{answer}\n\n📄 [Source Documents]:\n{source_texts}"
        except Exception:
            return "❌ An error occurred while processing the medical answer. Please try again later."

    return (
        "🌦️ I specialize in answering questions about medicine, health, and pharmacies. "
        "Could you please clarify if you want to know about a medicine, a pharmacy location, or something else?"
    )
