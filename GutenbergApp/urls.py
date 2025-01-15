from django.urls import path

from GutenbergApp import views

urlpatterns = [
    path("app/",views.temp_here,name="temp_here"),
    path("discover/", views.temp_somwhere, name="temp_somwhere"),

    path("book/", views.book_list, name='book_list'),  # Route principale pour la liste des livres
    path("book/<int:book_id>/", views.book_detail, name='book_detail'),
]