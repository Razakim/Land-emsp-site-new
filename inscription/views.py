from django.views.generic import TemplateView


class InscriptionLandingView(TemplateView):
    template_name = "inscription/landing.html"
