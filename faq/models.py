
from django.db import models
from django.core.cache import cache
from django.conf import settings
from ckeditor.fields import RichTextField
from googletrans import Translator
from django.core.exceptions import ValidationError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """Custom exception for translation failures"""
    pass

class FAQ(models.Model):
   
    question = models.TextField(
        help_text="Enter the question in English"
    )
    answer = RichTextField(
        help_text="Format your answer using the WYSIWYG editor"
    )
    
    # Language-specific fields with validation
    question_hi = models.TextField(blank=True, null=True)
    question_bn = models.TextField(blank=True, null=True)
    answer_hi = RichTextField(blank=True, null=True)
    answer_bn = RichTextField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    translation_status = models.JSONField(default=dict, 
        help_text="Tracks translation status for each language")

    SUPPORTED_LANGUAGES = ['en', 'hi', 'bn']

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]

    def __str__(self):
        return self.question[:50]

    def clean(self):
        if not self.question:
            raise ValidationError("Question field is required")
        if not self.answer:
            raise ValidationError("Answer field is required")

    def get_translated_field(self, field_name: str, lang: str) -> str:
       
        if lang not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {lang} is not supported")

        if lang == 'en':
            return getattr(self, field_name)

        cache_key = f'faq_{self.id}_{field_name}_{lang}'
        cached_value = cache.get(cache_key)
        
        if cached_value:
            return cached_value

        try:
            translated_field = f'{field_name}_{lang}'
            if hasattr(self, translated_field) and getattr(self, translated_field):
                value = getattr(self, translated_field)
            else:
                value = self._translate_text(getattr(self, field_name), lang)
                setattr(self, translated_field, value)
                self.save(update_fields=[translated_field])

            # Cache with varying timeout based on field type
            timeout = settings.CACHE_TIMEOUT_LONG if field_name == 'answer' else settings.CACHE_TIMEOUT
            cache.set(cache_key, value, timeout=timeout)
            
            return value

        except Exception as e:
            logger.error(f"Translation error for FAQ {self.id}: {str(e)}")
            return getattr(self, field_name)  # back to English

    def _translate_text(self, text: str, target_lang: str) -> str:
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                translator = Translator()
                translation = translator.translate(text, dest=target_lang)
                
                # UPdating translation status
                self.translation_status[target_lang] = {
                    'status': 'success',
                    'timestamp': timezone.now().isoformat()
                }
                self.save(update_fields=['translation_status'])
                
                return translation.text

            except Exception as e:
                logger.warning(f"Translation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    self.translation_status[target_lang] = {
                        'status': 'failed',
                        'error': str(e),
                        'timestamp': timezone.now().isoformat()
                    }
                    self.save(update_fields=['translation_status'])
                    raise TranslationError(f"Translation failed after {max_retries} attempts")

    def invalidate_cache(self):
        """Clear all cached translations for this FAQ"""
        for lang in self.SUPPORTED_LANGUAGES:
            for field in ['question', 'answer']:
                cache_key = f'faq_{self.id}_{field}_{lang}'
                cache.delete(cache_key)

    def save(self, *args, **kwargs):
        """Override save to handle cache invalidation and translations"""
        is_new = self._state.adding
        
        self.clean()
        
        if not is_new:
            self.invalidate_cache()
        
        super().save(*args, **kwargs)
        
        # Translation fro new FAQ
        if is_new:
            for lang in ['hi', 'bn']:
                try:
                    self.get_translated_field('question', lang)
                    self.get_translated_field('answer', lang)
                except Exception as e:
                    logger.error(f"Initial translation failed for {lang}: {str(e)}")