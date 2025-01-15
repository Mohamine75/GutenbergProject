from django.db import models

# Create your models here.
class Worldcities(models.Model):
    city = models.TextField(blank=True, null=True)
    lat = models.TextField(blank=True, null=True)  # This field type is a guess.
    lng = models.TextField(blank=True, null=True)  # This field type is a guess.
    country = models.TextField(blank=True, null=True)
    id = models.TextField(blank=True, primary_key=True)

    class Meta:
        managed = False
        db_table = 'worldcities'



class Book(models.Model):
    id = models.IntegerField(primary_key=True)  # Colonne id
    title = models.CharField(max_length=255)  # Colonne title
    author = models.CharField(max_length=255, null=True, blank=True)  # Colonne author
    content = models.TextField(null=True, blank=True)  # Colonne content

    class Meta:
        managed = False  # Désactive la gestion des migrations par Django
        db_table = 'books'  # Nom de la table dans la base de données
