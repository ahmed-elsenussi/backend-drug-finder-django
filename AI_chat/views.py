from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import traceback

from .utils import answer_question

@csrf_exempt
@require_POST
def ask_question(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        question = data.get("question", "").strip()

        if not question:
            return JsonResponse({"error": " Question is required."}, status=400)

        answer = answer_question(question)
        return JsonResponse({"answer": answer}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": " Invalid JSON format."}, status=400)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "error": "Internal server error.",
            "details": str(e)
        }, status=500)
