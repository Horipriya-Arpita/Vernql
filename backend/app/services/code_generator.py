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
1. Install dependencies: `pip install flask requests`
   Add your database driver, e.g. `pip install psycopg2-binary` for PostgreSQL
2. Set VERNQL_API_KEY, VERNQL_BASE_URL, and SCHEMA_ID at the top of the file
3. Implement `run_on_your_database(sql)` to connect to your own database
4. Run: `python app.py`
5. POST /query with {"question": "..."} — the full NL→SQL→run→visualize flow runs automatically
            """.strip(),

            "python_fastapi": """
1. Install dependencies: `pip install fastapi uvicorn httpx`
   Add your database driver, e.g. `pip install asyncpg` for async PostgreSQL
2. Set VERNQL_API_KEY, VERNQL_BASE_URL, and SCHEMA_ID at the top of the file
3. Implement `run_on_your_database(sql)` to connect to your own database
4. Run: `uvicorn main:app --reload`
5. Docs at http://localhost:8000/docs — POST /query for the full flow
            """.strip(),

            "python_django": """
1. Install dependencies: `pip install django requests`
   Add your database driver, e.g. `pip install psycopg2-binary` for PostgreSQL
2. Add VERNQL_API_KEY, VERNQL_BASE_URL, VERNQL_SCHEMA_ID to settings.py
3. Implement `run_on_your_database(sql)` — example using Django's own connection is in the file
4. Wire query_view and health_view into your urls.py (see bottom of file)
5. POST /api/query/ with {"question": "..."} for the full flow
            """.strip(),

            "nodejs_express": """
1. Install dependencies: `npm install express axios`
   Add your database driver, e.g. `npm install pg` for PostgreSQL
2. Set VERNQL_API_KEY, VERNQL_BASE_URL, and SCHEMA_ID at the top of the file
3. Implement `runOnYourDatabase(sql)` — example using `pg` is in the file
4. Run: `node server.js`
5. POST /query with {"question": "..."} for the full flow
            """.strip(),

            "php": """
1. Ensure the PHP curl extension is enabled (php-curl)
   Add your database extension, e.g. php-pgsql for PostgreSQL
2. Set VERNQL_API_KEY, VERNQL_BASE_URL, and SCHEMA_ID at the top of the file
3. Implement `run_on_your_database($sql)` — example using PDO is in the file
4. Deploy to your PHP server
5. POST /query.php with {"question": "..."} for the full flow
            """.strip(),

            "curl": """
1. Replace the API_KEY and SCHEMA_ID variables at the top of the script
2. Follow the 4-step flow in order: session → SQL → execute → submit results
3. Implement Step 3 with your real database CLI (psql, mysql, etc.)
4. The script requires python3 for JSON parsing (or adapt to jq)
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
