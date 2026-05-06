from django.contrib import admin

from .models import SlideCarousel


@admin.register(SlideCarousel)
class SlideCarouselAdmin(admin.ModelAdmin):
    list_display = ("titre", "ordre", "actif")
    list_editable = ("ordre", "actif")
    search_fields = ("titre",)
