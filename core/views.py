from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"

    fallback_slides = [
        {"titre": "Campus EMSP", "image": "lezir/images/hero-5-bg-img.jpg"},
        {"titre": "Vie academique", "image": "lezir/images/features-img.png"},
        {"titre": "Mediatheque", "image": "lezir/images/features-img-1.png"},
        {"titre": "Excellence EMSP", "image": "lezir/images/hero-1-bg-img.png"},
    ]

    @staticmethod
    def _title_from_filename(filename):
        return filename.replace("-", " ").replace("_", " ").strip().title()

    def _count_model(self, app_label, model_name, **filters):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            return 0
        if model is None:
            return 0
        queryset = model.objects.all()
        model_fields = {field.name for field in model._meta.fields}
        clean_filters = {key: value for key, value in filters.items() if key.split("__")[0] in model_fields}
        if clean_filters:
            queryset = queryset.filter(**clean_filters)
        return queryset.count()

    def _recent_documents(self):
        try:
            model = apps.get_model("bibliotheque", "Document")
        except LookupError:
            return []
        if model is None:
            return []

        docs = model.objects.all()
        if "valide" in {field.name for field in model._meta.fields}:
            docs = docs.filter(valide=True)
        if "date_ajout" in {field.name for field in model._meta.fields}:
            docs = docs.order_by("-date_ajout")
        return list(docs[:5])

    def _slides(self):
        try:
            model = apps.get_model("core", "SlideCarousel")
        except LookupError:
            return self.fallback_slides
        if model is None:
            return self.fallback_slides
        slides_qs = list(model.objects.filter(actif=True).order_by("ordre", "id")[:6])
        if not slides_qs:
            return self.fallback_slides
        slides = []
        for slide in slides_qs:
            image_url = getattr(getattr(slide, "image", None), "url", None)
            if not image_url:
                continue
            slides.append({"titre": slide.titre, "image": image_url.lstrip("/")})
        return slides or self.fallback_slides

    def _partner_logos(self):
        logos_dir = settings.BASE_DIR / "static" / "img" / "home" / "partenaires"
        if not logos_dir.exists() or not logos_dir.is_dir():
            return []

        allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
        logos = []
        for logo_file in sorted(logos_dir.iterdir(), key=lambda path: path.name.lower()):
            if not logo_file.is_file():
                continue
            if logo_file.suffix.lower() not in allowed_extensions:
                continue
            label = logo_file.stem.replace("-", " ").replace("_", " ").strip()
            logos.append(
                {
                    "path": f"img/home/partenaires/{logo_file.name}",
                    "alt": label.title() if label else "Partenaire",
                }
            )
        return logos

    def _first_image_in_folder(self, folder_name):
        folder = settings.BASE_DIR / "static" / "img" / "home" / folder_name
        if not folder.exists() or not folder.is_dir():
            return None

        allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
        files = sorted(
            [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in allowed_extensions],
            key=lambda path: path.name.lower(),
        )
        if not files:
            return None
        return f"img/home/{folder_name}/{files[0].name}"

    def _home_mediatheque_previews(self):
        photos_dir = settings.BASE_DIR / "static" / "img" / "home" / "phototheque"
        videos_dir = settings.BASE_DIR / "static" / "videos" / "mediatheque"

        photo_exts = {".png", ".jpg", ".jpeg", ".webp"}
        video_exts = {".mp4", ".webm", ".ogg", ".mov", ".m4v"}

        photos = []
        if photos_dir.exists() and photos_dir.is_dir():
            for media_file in sorted(photos_dir.iterdir(), key=lambda p: p.name.lower()):
                if media_file.is_file() and media_file.suffix.lower() in photo_exts:
                    photos.append(
                        {
                            "path": f"img/home/phototheque/{media_file.name}",
                            "title": self._title_from_filename(media_file.stem),
                        }
                    )
        photos = photos[:3]

        videos = []
        if videos_dir.exists() and videos_dir.is_dir():
            for media_file in sorted(videos_dir.iterdir(), key=lambda p: p.name.lower()):
                if media_file.is_file() and media_file.suffix.lower() in video_exts:
                    videos.append(
                        {
                            "path": f"videos/mediatheque/{media_file.name}",
                            "title": self._title_from_filename(media_file.stem),
                        }
                    )
        videos = videos[:3]

        fallback_poster = "img/home/autres/presentation.jpg"
        for index, video in enumerate(videos):
            if photos:
                video["poster"] = photos[index % len(photos)]["path"]
            else:
                video["poster"] = fallback_poster

        return photos, videos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        user_fields = {field.name for field in User._meta.fields}
        if "role" in user_fields:
            nb_etudiants = User.objects.filter(role="etudiant").count()
        else:
            nb_etudiants = User.objects.count()
        media_photos, media_videos = self._home_mediatheque_previews()

        context.update(
            {
                "nb_filieres": self._count_model("core", "Filiere", active=True) or self._count_model("core", "Filiere"),
                "nb_licences": self._count_model("core", "Licence"),
                "nb_documents": self._count_model("bibliotheque", "Document", valide=True)
                or self._count_model("bibliotheque", "Document"),
                "nb_etudiants": nb_etudiants,
                "slides": self._slides(),
                "partner_logos": self._partner_logos(),
                "directeur_general_image": self._first_image_in_folder("directeur_general"),
                "directeur_etudes_image": self._first_image_in_folder("directeur_etudes"),
                "media_photos_preview": media_photos,
                "media_videos_preview": media_videos,
                "derniers_documents": self._recent_documents(),
                "home_active": "home",
            }
        )
        return context


class InstitutionView(TemplateView):
    template_name = "core/institution.html"


class FormationsView(TemplateView):
    template_name = "core/formations.html"


class FaqView(TemplateView):
    template_name = "core/faq.html"


class JournalView(TemplateView):
    template_name = "core/journal.html"


class ConcoursView(TemplateView):
    template_name = "core/concours.html"


class MediathequeView(TemplateView):
    template_name = "core/mediatheque.html"

    def _list_static_media(self, folder_parts, allowed_exts):
        folder = settings.BASE_DIR / "static"
        for part in folder_parts:
            folder = folder / part

        if not folder.exists() or not folder.is_dir():
            return []

        media = []
        for media_file in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if not media_file.is_file():
                continue
            if media_file.suffix.lower() not in allowed_exts:
                continue
            label = media_file.stem.replace("-", " ").replace("_", " ").strip().title()
            rel_path = "/".join([*folder_parts, media_file.name])
            media.append({"title": label or media_file.name, "path": rel_path})
        return media

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photos = self._list_static_media(("img", "home", "phototheque"), {".png", ".jpg", ".jpeg", ".webp"})
        videos = self._list_static_media(("videos", "mediatheque"), {".mp4", ".webm", ".ogg", ".mov", ".m4v"})

        photo_fallback = "img/home/autres/presentation.jpg"
        for index, video in enumerate(videos):
            if photos:
                video["poster"] = photos[index % len(photos)]["path"]
            else:
                video["poster"] = photo_fallback

        context.update(
            {
                "photos": photos,
                "videos": videos,
            }
        )
        return context
