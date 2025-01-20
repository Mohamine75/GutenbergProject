from datetime import datetime

import geocoder
import requests
from django.http import HttpResponse
from django.template import loader

from GutenbergApp.models import Worldcities,Book
from django.shortcuts import render

from .regex_search_impl import RegexSearcher

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

def simple_search(query):
        # Première requête pour les résultats de recherche directs
    search_results = Book.objects.raw('''
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
    
    # Convertir en liste pour pouvoir compter et réutiliser
    search_results = list(search_results)
    count = len(search_results)
    message = f"{count} livre(s) correspondent ! Triés par score de pertinence." if count > 0 else "Aucun livre ne correspond !"
    return (search_results, count, message)

def regex_search(query):
    searcher = RegexSearcher()
    
    # Obtenir les résultats bruts (book_id, occurrences, closeness_score)
    raw_results = searcher.search_pattern(query)
    
    if not raw_results:
        return [], 0, "Aucun livre ne correspond !"
        
    # Calculer max_occurrences pour la normalisation
    max_occurrences = max(occ for _, occ, _ in raw_results)
    
    # Créer la liste des livres avec leur score
    search_results = []
    for book_id, occurrences, closeness_score in raw_results:
        book = Book.objects.get(id=book_id)
        # Calcul du score final comme dans simple_search
        normalized_occurrences = (occurrences / max_occurrences) if max_occurrences > 0 else 0
        final_score = 50 * closeness_score + 50 * normalized_occurrences
        
        # Ajouter les attributs nécessaires à l'objet book
        book.occurrences = occurrences
        book.closeness_score = closeness_score
        book.final_score = final_score
        
        search_results.append(book)
    
    # Trier par score final
    search_results.sort(key=lambda x: x.final_score, reverse=True)
    count = len(search_results)
    message = f"{count} livre(s) correspondent ! Triés par score de pertinence."
    
    return search_results, count, message

def search_books(request):
    """
    Recherche les livres contenant le mot donné et suggère 2 livres similaires
    pour chacun des 3 premiers résultats de recherche.
    """
    query = request.GET.get('search-simple', '').strip().lower()
    search_results = []
    suggestions = []
    message = ""
    
    if query:
        # Première requête pour les résultats de recherche directs
        search_results = Book.objects.raw('''
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
        
        if any(c in query for c in '*|+()'):
            # Recherche avancée (regex)
            print(query)
            res = regex_search(query)
        else:
            # Simple recherche de mot
            res = simple_search(query)

        # Convertir en liste pour pouvoir compter et réutiliser
        search_results = res[0]
        count = res[1]
        message = res[2]

        # Si on a des résultats, chercher des suggestions pour les 3 premiers
        if count > 0:
            # On prend les IDs des 3 premiers livres trouvés au maximum
            top_book_ids = [book.id for book in search_results[:3]]
            
            # Construction de la chaîne de paramètres pour la clause IN
            placeholders = ','.join(['%s'] * len(top_book_ids))
            
            # Deuxième requête pour les suggestions
            query_params = top_book_ids + top_book_ids + top_book_ids + top_book_ids  # On a besoin des IDs 4 fois
            
            suggestions = Book.objects.raw(f'''
                WITH RankedSimilarBooks AS (
                    SELECT 
                        source_book_id as origin_book_id,
                        target_book_id as suggested_book_id,
                        similarity_score,
                        ROW_NUMBER() OVER (
                            PARTITION BY source_book_id 
                            ORDER BY similarity_score DESC
                        ) as rank
                    FROM similarity_edges
                    WHERE source_book_id IN ({placeholders})
                    AND target_book_id NOT IN ({placeholders})
                    
                    UNION ALL
                    
                    SELECT 
                        target_book_id as origin_book_id,
                        source_book_id as suggested_book_id,
                        similarity_score,
                        ROW_NUMBER() OVER (
                            PARTITION BY target_book_id 
                            ORDER BY similarity_score DESC
                        ) as rank
                    FROM similarity_edges
                    WHERE target_book_id IN ({placeholders})
                    AND source_book_id NOT IN ({placeholders})
                )
                SELECT 
                    b.*,
                    r.similarity_score,
                    r.origin_book_id
                FROM RankedSimilarBooks r
                INNER JOIN books b ON b.id = r.suggested_book_id
                WHERE rank <= 2
                ORDER BY r.origin_book_id, r.similarity_score DESC
            ''', query_params)
            
            suggestions = list(set(suggestions))

                        # Fonction temporaire de debug
            def debug_print_suggestions():
                print("\n=== SUGGESTIONS DEBUG ===")
                for sugg in suggestions:
                    print(f"Pour le livre {sugg.origin_book_id} -> Suggestion: {sugg.title} (score: {sugg.similarity_score})")
                print("========================\n")
            
            debug_print_suggestions()
    
    return render(request, 'book_list.html', {
        'books': search_results,
        'suggestions': suggestions,
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
