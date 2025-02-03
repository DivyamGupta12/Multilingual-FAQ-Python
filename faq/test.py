
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.cache import cache
from unittest.mock import patch
from .models import FAQ, TranslationError
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestFAQSystem:
    @pytest.fixture
    def api_client(self):
        user = User.objects.create_user(username='testuser', password='testpass')
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def sample_faq(self):
        return FAQ.objects.create(
            question="What is your return policy for international orders?",
            answer="You can return international orders within 30 days of delivery."
        )

    def test_model_validation(self):
        with pytest.raises(ValidationError):
            FAQ.objects.create(question="", answer="")

    def test_translation_with_retry(self, sample_faq):
        with patch('googletrans.Translator.translate') as mock_translate:
           
            mock_translate.side_effect = [
                Exception("Network error"),
                Exception("Timeout"),
                type('obj', (), {'text': 'Translated text'})
            ]
            
            result = sample_faq._translate_text("Test text", "hi")
            assert result == "Translated text"
            assert mock_translate.call_count == 3

    def test_cache_invalidation(self, sample_faq):
        # Set up cache
        cache_key = f'faq_{sample_faq.id}_question_hi'
        cache.set(cache_key, "Cached translation")
        
        assert cache.get(cache_key) == "Cached translation"
        
        # Update FAQ
        sample_faq.question = "Updated question"
        sample_faq.save()
        
        assert cache.get(cache_key) is None

    @pytest.mark.parametrize("lang", ['en', 'hi', 'bn'])
    def test_api_language_support(self, api_client, sample_faq, lang):
        url = reverse('faq-list')
        response = api_client.get(f"{url}?lang={lang}")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        
        if lang == 'en':
            assert response.data[0]['question'] == sample_faq.question
        else:
            assert response.data[0]['question'] != sample_faq.question
            assert response.data[0]['translations_available'][lang]

    def test_refresh_translation_endpoint(self, api_client, sample_faq):
        url = reverse('faq-refresh-translation', kwargs={'pk': sample_faq.id})
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'translation_status' in response.data
        assert response.data['message'] == "Translations refreshed successfully"

    def test_api_error_handling(self, api_client):
        url = reverse('faq-list')
        response = api_client.get(f"{url}?lang=invalid")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    @pytest.mark.parametrize("field,value,valid", [
        ('question', 'Short', False),
        ('question', 'This is a valid question?', True),
        ('answer', 'Too short', False),
        ('answer', 'This is a proper answer that provides good information.', True),
    ])
    def test_field_validation(self, api_client, field, value, valid):
        url = reverse('faq-list')
        data = {
            'question': 'Default valid question for testing?',
            'answer': 'Default valid answer for testing purposes.'
        }
        data[field] = value
        
        response = api_client.post(url, data, format='json')
        assert (response.status_code == status.HTTP_201_CREATED) == valid