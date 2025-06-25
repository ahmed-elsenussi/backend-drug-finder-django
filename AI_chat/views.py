from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import traceback

from .utils import answer_question, web_search_fallback

@csrf_exempt
def ask_question(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question", "")

            if not question:
                return JsonResponse({"error": "Question is required."}, status=400)

            # استخدام RAG system مع الدالة الجديدة
            result = answer_question(question)

            # fallback لو مفيش إجابة (موجود بالفعل في answer_question)
            return JsonResponse({"answer": result})

        except Exception as e:
            traceback.print_exc()  # طباعة الخطأ في الكونسول
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)
