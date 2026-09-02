from django.http import HttpResponse


def home(request):
    return HttpResponse("Zoomcamp AI Chores")
