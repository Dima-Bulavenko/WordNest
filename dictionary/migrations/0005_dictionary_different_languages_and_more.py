# Generated by Django 5.0.4 on 2024-07-06 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary', '0004_language_translation_dictionary_word_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='dictionary',
            constraint=models.CheckConstraint(check=models.Q(('source_language', models.F('target_language')), _negated=True), name='different_languages'),
        ),
        migrations.AddConstraint(
            model_name='dictionary',
            constraint=models.UniqueConstraint(fields=('user', 'source_language', 'target_language'), name='unique_language_pair_per_user'),
        ),
    ]
