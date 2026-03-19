"""
Code Generator Service
Generates integration code snippets for various languages and frameworks
"""
from typing import Dict, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import structlog

logger = structlog.get_logger()


class CodeGenerator:
    """
    Generates integration code snippets for the TextSQL API

    Supports multiple languages and frameworks:
    - Python (Flask, FastAPI, Django)
    - Node.js (Express)
    - PHP
    - cURL (for testing)
    """

    SUPPORTED_LANGUAGES = {
        "python_flask": "Python with Flask",
        "python_fastapi": "Python with FastAPI",
        "python_django": "Python with Django",
        "nodejs_express": "Node.js with Express",
        "php": "PHP",
        "curl": "cURL (Command Line)"
    }

    def __init__(self):
        """Initialize code generator with Jinja2 template engine"""
        self.logger = logger.bind(service="code_generator")

        # Set up Jinja2 template environment
        template_dir = Path(__file__).parent.parent / "templates" / "snippets"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

        self.logger.debug("CodeGenerator initialized", template_dir=str(template_dir))

    def generate_snippet(
        self,
        language: str,
        api_key: str,
        base_url: str = "http://localhost:8000",
        schema_id: Optional[str] = None,
        query_example: str = "Show all users created in the last 30 days"
    ) -> Dict[str, str]:
        """
        Generate integration code snippet

        Args:
            language: Language/framework identifier (e.g., 'python_flask')
            api_key: API key for authentication
            base_url: Base URL of the API
            schema_id: Optional schema ID for examples
            query_example: Example natural language query

        Returns:
            Dictionary with 'code' and 'language' keys

        Raises:
            ValueError: If language is not supported
        """
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported: {', '.join(self.SUPPORTED_LANGUAGES.keys())}"
            )

        # Prepare template context
        context = {
            "api_key": api_key,
            "base_url": base_url,
            "schema_id": schema_id or "your-schema-id-here",
            "query_example": query_example,
            "api_version": "v1"
        }

        try:
            # Load and render template
            template = self.env.get_template(f"{language}.jinja2")
            code = template.render(**context)

            self.logger.info(
                "Code snippet generated",
                language=language,
                code_length=len(code)
            )

            return {
                "code": code,
                "language": language,
                "language_name": self.SUPPORTED_LANGUAGES[language],
                "instructions": self._get_instructions(language)
            }

        except TemplateNotFound:
            self.logger.error("Template not found", language=language)
            raise ValueError(f"Template for {language} not found")
        except Exception as e:
            self.logger.error("Code generation failed", error=str(e), language=language)
            raise

    def generate_all_snippets(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        schema_id: Optional[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate code snippets for all supported languages

        Args:
            api_key: API key for authentication
            base_url: Base URL of the API
            schema_id: Optional schema ID

        Returns:
            Dictionary mapping language to snippet data
        """
        snippets = {}

        for language in self.SUPPORTED_LANGUAGES.keys():
            try:
                snippets[language] = self.generate_snippet(
                    language=language,
                    api_key=api_key,
                    base_url=base_url,
                    schema_id=schema_id
                )
            except Exception as e:
                self.logger.warning(
                    "Failed to generate snippet",
                    language=language,
                    error=str(e)
                )

        return snippets

    def _get_instructions(self, language: str) -> str:
        """Get setup instructions for a specific language"""
        instructions = {
            "python_flask": """
1. Install required packages: `pip install requests flask`
2. Set your API key in the code
3. Run the Flask app: `python app.py`
4. Access the endpoint at http://localhost:5000/query
            """.strip(),

            "python_fastapi": """
1. Install required packages: `pip install requests fastapi uvicorn`
2. Set your API key in the code
3. Run the FastAPI app: `uvicorn main:app --reload`
4. Access the endpoint at http://localhost:8000/query
            """.strip(),

            "python_django": """
1. Install required packages: `pip install requests django`
2. Set your API key in Django settings
3. Add the view to your urls.py
4. Run the server: `python manage.py runserver`
            """.strip(),

            "nodejs_express": """
1. Install required packages: `npm install express axios`
2. Set your API key in the code
3. Run the server: `node server.js`
4. Access the endpoint at http://localhost:3000/query
            """.strip(),

            "php": """
1. Ensure PHP curl extension is enabled
2. Set your API key in the code
3. Deploy to your PHP server
4. Access the endpoint via HTTP POST
            """.strip(),

            "curl": """
1. Replace YOUR_API_KEY with your actual API key
2. Replace your-schema-id with your schema UUID
3. Run the command in your terminal
            """.strip()
        }

        return instructions.get(language, "No specific instructions available")

    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages with descriptions"""
        return self.SUPPORTED_LANGUAGES.copy()

    def validate_snippet_syntax(self, language: str, code: str) -> bool:
        """
        Basic syntax validation for generated code

        Args:
            language: Language identifier
            code: Generated code

        Returns:
            True if code appears valid, False otherwise
        """
        # Basic checks
        if not code or len(code) < 50:
            return False

        # Language-specific checks
        validators = {
            "python_flask": lambda c: "import" in c and "Flask" in c and "requests" in c,
            "python_fastapi": lambda c: "import" in c and "FastAPI" in c,
            "python_django": lambda c: "import" in c and "django" in c.lower(),
            "nodejs_express": lambda c: "require" in c and "express" in c,
            "php": lambda c: "<?php" in c and "curl_init" in c,
            "curl": lambda c: "curl" in c and "-X POST" in c
        }

        validator = validators.get(language)
        if validator:
            return validator(code)

        return True  # Default to valid if no validator

    def get_snippet_file_extension(self, language: str) -> str:
        """Get appropriate file extension for a language"""
        extensions = {
            "python_flask": "py",
            "python_fastapi": "py",
            "python_django": "py",
            "nodejs_express": "js",
            "php": "php",
            "curl": "sh"
        }
        return extensions.get(language, "txt")
