from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import FAQ
from .serializers import FAQSerializer
import logging

logger = logging.getLogger(__name__)

class FAQViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing FAQs with multilingual support.
    Includes caching and comprehensive error handling.
    """
    queryset = FAQ.objects.filter(is_active=True)
    serializer_class = FAQSerializer
    permission_classes = [IsAuthenticated]

    lang_param = openapi.Parameter(
        'lang', openapi.IN_QUERY,
        description="Language code (en, hi, bn)",
        type=openapi.TYPE_STRING
    )

    @swagger_auto_schema(manual_parameters=[lang_param])
    @method_decorator(cache_page(60 * 15))  # 15 minutes cache
    def list(self, request, *args, **kwargs):
        
        try:
            lang = request.query_params.get('lang', 'en')
            if lang not in FAQ.SUPPORTED_LANGUAGES:
                return Response(
                    {"error": f"Language {lang} not supported"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            queryset = self.get_queryset()
            serializer = self.get_serializer(
                queryset, 
                many=True, 
                context={'lang': lang}
            )
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in FAQ list: {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def refresh_translation(self, request, pk=None):
        
        try:
            faq = self.get_object()
            faq.invalidate_cache()
            
            for lang in ['hi', 'bn']:
                faq.get_translated_field('question', lang)
                faq.get_translated_field('answer', lang)
            
            return Response({
                "message": "Translations refreshed successfully",
                "translation_status": faq.translation_status
            })

        except Exception as e:
            logger.error(f"Translation refresh error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
