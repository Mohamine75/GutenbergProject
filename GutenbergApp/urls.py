from django.urls import path

from GutenbergApp import views

urlpatterns = [
    path('search/', views.search_books, name='search_books'),

    path("book/", views.book_list, name='book_list'),  # Route principale pour la liste des livres
    path("book/<int:book_id>/", views.book_detail, name='book_detail'),
]