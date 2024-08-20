from django.shortcuts import render

def api_overview(request):
    return render(request, 'api_overview.html')
