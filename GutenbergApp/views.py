from datetime import datetime

import geocoder
import requests
from django.http import HttpResponse
from django.template import loader

from GutenbergApp.models import Worldcities,Book
from django.shortcuts import render


# Create your views here.
def book_list(request):
    """Affiche la liste des livres disponibles."""
    books = Book.objects.all()
    return render(request, 'book_list.html', {'books': books})


def book_detail(request, book_id):
    """Affiche les détails d'un livre."""
    try:
        book = Book.objects.get(id=book_id)

        # Remplacer les doubles sauts de ligne par des balises <p>
        paragraphs = book.content.split('\n\n')
        formatted_content = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs])

        return render(request, 'book_detail.html', {'book': book, 'formatted_content': formatted_content})
    except Book.DoesNotExist:
        return render(request, '404.html', status=404)




def search_books(request):
    """Recherche les livres contenant exactement le mot donné."""
    query = request.GET.get('search-simple', '').strip()
    books = []
    message = ""
    if query:
        # Utilise regex pour chercher le mot exact (avec word boundaries \b)
        books = Book.objects.filter(content__regex=r'\b' + query + r'\b')
        count = books.count()
        message = f"{count} livre(s) correspondent !" if count > 0 else "Aucun livre ne correspond !"
        print(books)
    return render(request, 'book_list.html', {'books': books, 'message': message})

def temp_somwhere(request):
    random_item = Worldcities.objects.all().order_by('?').first()
    city = random_item.city
    location = [random_item.lat,random_item.lng]
    temp = get_temp(location)
    template = loader.get_template('index.html')
    context = {'city': city, 'temp': temp}
    return HttpResponse(template.render(context, request))

def temp_here(request):
    location  = geocoder.ip('me').latlng
    temp = get_temp(location)
    template = loader.get_template("index.html")
    context = {'city' : 'Your location',
               'temp' : temp}
    return HttpResponse(template.render(context, request))

def get_temp(location):
    endpoint = ("https://api.open-meteo.com/v1/forecast");
    api_request = f"{endpoint}?latitude={location[0]}&longitude={location[1]}&hourly=temperature_2m"
    now = datetime.now()
    hour = now.hour
    meteo_data = requests.get(api_request).json()
    temp = meteo_data['hourly']['temperature_2m'][hour]
    return temp
