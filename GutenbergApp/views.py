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
    """
    Recherche les livres contenant le mot donné en utilisant un score combiné:
    - 50% basé sur le closeness_score (centralité)
    - 50% basé sur le nombre d'occurrences normalisé
    """
    query = request.GET.get('search-simple', '').strip().lower()
    books = []
    message = ""
    
    if query:
        # Requête SQL avec calcul du score combiné
        books = Book.objects.raw('''
            WITH max_occurrences AS (
                SELECT MAX(occurrences) as max_occ
                FROM word_count
                WHERE word = %s
            )
            SELECT 
                b.*, 
                wc.occurrences,
                cm.closeness_score,
                (50 * cm.closeness_score + 50 * (CAST(wc.occurrences AS FLOAT) / 
                    CAST(max_occ AS FLOAT))) as final_score
            FROM books b
            INNER JOIN word_count wc ON b.id = wc.book_id
            INNER JOIN centrality_measures cm ON b.id = cm.book_id
            CROSS JOIN max_occurrences
            WHERE wc.word = %s
            ORDER BY final_score DESC
        ''', [query, query])
        
        count = len(list(books))
        message = f"{count} livre(s) correspondent ! Triés par score de pertinence." if count > 0 else "Aucun livre ne correspond !"
    
    return render(request, 'book_list.html', {
        'books': books, 
        'message': message,
        'query': query
    })

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
