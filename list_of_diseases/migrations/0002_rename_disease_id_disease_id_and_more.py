# Generated by Django 4.2.4 on 2023-12-07 14:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('list_of_diseases', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='disease',
            old_name='disease_id',
            new_name='id',
        ),
        migrations.RenameField(
            model_name='medical_drug',
            old_name='drug_id',
            new_name='id',
        ),
        migrations.RenameField(
            model_name='sphere',
            old_name='sphere_id',
            new_name='id',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='user_id',
            new_name='id',
        ),
        migrations.AlterField(
            model_name='medical_drug',
            name='user_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='list_of_diseases.customuser'),
        ),
    ]