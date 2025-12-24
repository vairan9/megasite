from django.shortcuts import render

# Create your views here.
def portfolio(request):
    return render(request, 'portfolio.html')

def website(request):
    return render(request, 'infiniti_vacation/page.html')