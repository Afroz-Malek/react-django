from django.http import JsonResponse

def fyers_callback(request):
    """
    Handles Fyers redirect after successful auth.
    Example URL:
    http://127.0.0.1:9000/fyers-callback/?s=ok&code=200&auth_code=XYZ
    """
    auth_code = request.GET.get("auth_code")
    status_code = request.GET.get("code")
    state = request.GET.get("state")

    return JsonResponse({
        "message": "Fyers redirect received",
        "auth_code": auth_code,
        "status_code": status_code,
        "state": state
    })
