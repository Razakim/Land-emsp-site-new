from django.db import models


class SlideCarousel(models.Model):
    titre = models.CharField(max_length=150)
    image = models.ImageField(upload_to="carousel/")
    ordre = models.PositiveIntegerField(default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ("ordre", "id")

    def __str__(self):
        return self.titre
