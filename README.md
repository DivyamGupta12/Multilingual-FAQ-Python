# Multilingual FAQ System

A Django-based FAQ management system with multilingual support, WYSIWYG editing, and efficient caching.

## Directory structure
.

├── Dockerfile

├── docker-compose.yml

├── requirements.txt

├── core/

│   ├── __init__.py

│   ├── settings.py

│   ├── urls.py

│   └── wsgi.py

├── faq/

│   ├── __init__.py

│   ├── admin.py

│   ├── apps.py

│   ├── models.py

│   ├── serializers.py

│   ├── tests.py

│   ├── urls.py

│   └── views.py

└── README.md




## Features

- Multilingual FAQ management (English, Hindi, Bengali)
- WYSIWYG editor support using CKEditor
- Automatic translation using Google Translate API
- Redis-based caching for improved performance
- RESTful API with language selection
- Comprehensive admin interface
- Docker support for easy deployment

## Installation

1. Clone the repository:
```bash
git clone https://github.com/DivyamGupta12/multilingual-faq.git
cd multilingual-faq
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## API Usage

### Fetch FAQs

```bash
# Get FAQs in English (default)
curl http://localhost:8000/api/faqs/

# Get FAQs in Hindi
curl http://localhost:8000/api/faqs/?lang=hi

# Get FAQs in Bengali
curl http://localhost:8000/api/faqs/?lang=bn
```

### Create FAQ

```bash
curl -X POST http://localhost:8000/api/faqs/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your return policy?", "answer": "You can return items within 30 days."}'
```

## Docker Deployment

1. Build the Docker image:
```bash
docker-compose build
```

2. Start the services:
```bash
docker-compose up -d
```

## Testing

Run the test suite:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
