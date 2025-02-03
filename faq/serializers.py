from rest_framework import serializers
from .models import FAQ
from django.utils.translation import gettext_lazy as _

class FAQSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    answer = serializers.SerializerMethodField()
    translations_available = serializers.SerializerMethodField()
    translation_status = serializers.JSONField(read_only=True)

    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'answer', 'translations_available',
            'translation_status', 'created_at', 'updated_at'
        ]

    def get_question(self, obj):
        lang = self.context.get('lang', 'en')
        return obj.get_translated_field('question', lang)

    def get_answer(self, obj):
        lang = self.context.get('lang', 'en')
        return obj.get_translated_field('answer', lang)

    def get_translations_available(self, obj):
        return {
            lang: bool(getattr(obj, f'question_{lang}', None))
            for lang in obj.SUPPORTED_LANGUAGES if lang != 'en'
        }

    def validate_question(self, value):
        if len(value) < 10:
            raise serializers.ValidationError(
                _("Question must be at least 10 characters long")
            )
        return value

    def validate_answer(self, value):
        if len(value) < 20:
            raise serializers.ValidationError(
                _("Answer must be at least 20 characters long")
            )
        return value