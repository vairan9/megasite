from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Apartment

def home(request):
    apartments = Apartment.objects.filter(is_active=True).order_by("name")
    return render(request, "infiniti_vacation/page.html", {"apartments": apartments})