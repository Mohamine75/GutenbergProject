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
    gutenberg_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()

    def __str__(self):
        return f"{self.title} by {self.author or 'Unknown Author'}"

