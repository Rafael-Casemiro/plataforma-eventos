from django.db import models
from django.conf import settings



class Event(models.Model):
     title = models.CharField(max_length=255, verbose_name='titulo')
     organizer = models.ForeignKey(
          settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events"
     )
     description = models.TextField(blank=True, verbose_name='descricao')
     date = models.DateTimeField()
     location = models.CharField(max_length=255, verbose_name='local')
     capacity = models.PositiveIntegerField()
     price = models.DecimalField(max_digits=8, decimal_places=2)
     external_ref = models.IntegerField()
     external_title = models.CharField(max_length=255, blank=True)
     poster_path = models.CharField(max_length=255, blank=True)
     is_published = models.BooleanField(default=False)
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)

     class Meta:
          verbose_name = 'Evento'
          verbose_name_plural = 'Eventos'

     def __str__(self):
          return self.title