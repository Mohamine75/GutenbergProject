# Generated by Django 5.1.4 on 2025-01-20 09:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('GutenbergApp', '0002_alter_book_options'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='book',
            table='books',
        ),
    ]
