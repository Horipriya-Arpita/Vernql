"""
Integration Code Snippets Endpoints
Generate code snippets for integrating TextSQL API
"""
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import CurrentCompany, CurrentCompanyEither
from app.services.code_generator import CodeGenerator

router = APIRouter(prefix="/integrations", tags=["Integrations"])


class SnippetRequest(BaseModel):
    """Request schema for code snippet generation"""
    language: str = Field(
        ...,
        description="Language/framework identifier",
        example="python_flask"
    )
    schema_id: Optional[str] = Field(
        None,
        description="Optional schema ID to include in example"
    )
    base_url: Optional[str] = Field(
        "http://localhost:8000",
        description="Base URL of the TextSQL API"
    )


class SnippetResponse(BaseModel):
    """Response schema for generated code snippet"""
    code: str = Field(..., description="Generated code snippet")
    language: str = Field(..., description="Language identifier")
    language_name: str = Field(..., description="Human-readable language name")
    instructions: str = Field(..., description="Setup instructions")
    file_extension: str = Field(..., description="Recommended file extension")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "# Python code here...",
                "language": "python_flask",
                "language_name": "Python with Flask",
                "instructions": "1. Install dependencies...",
                "file_extension": "py"
            }
        }


class LanguagesResponse(BaseModel):
    """Response schema for supported languages"""
    languages: Dict[str, str] = Field(..., description="Map of language ID to name")

    class Config:
        json_schema_extra = {
            "example": {
                "languages": {
                    "python_flask": "Python with Flask",
                    "python_fastapi": "Python with FastAPI",
                    "nodejs_express": "Node.js with Express"
                }
            }
        }


class AllSnippetsResponse(BaseModel):
    """Response schema for all snippets"""
    snippets: Dict[str, SnippetResponse] = Field(
        ...,
        description="Map of language to snippet data"
    )


@router.get(
    "/languages",
    response_model=LanguagesResponse,
    summary="Get supported languages"
)
async def get_supported_languages():
    """
    Get list of supported languages/frameworks for code generation

    Returns a dictionary mapping language identifiers to human-readable names.

    ## Supported Languages

    - **python_flask**: Python with Flask framework
    - **python_fastapi**: Python with FastAPI framework
    - **python_django**: Python with Django framework
    - **nodejs_express**: Node.js with Express framework
    - **php**: PHP (vanilla)
    - **curl**: cURL commands for testing

    ## Response

    Returns map of language IDs to descriptive names
    """
    generator = CodeGenerator()
    languages = generator.get_supported_languages()

    return LanguagesResponse(languages=languages)


@router.post(
    "/snippet",
    response_model=SnippetResponse,
    summary="Generate integration code snippet"
)
async def generate_snippet(
    request: SnippetRequest,
    company: CurrentCompanyEither
):
    """
    Generate integration code snippet for a specific language

    Creates ready-to-use code that demonstrates how to integrate
    the TextSQL API into your application.

    ## Features

    - Complete working examples
    - Proper error handling
    - Authentication included
    - Comments and documentation
    - Copy-paste ready

    ## Parameters

    - **language**: Language/framework identifier (see /languages endpoint)
    - **schema_id**: Optional schema ID to use in examples
    - **base_url**: API base URL (default: http://localhost:8000)

    ## Response

    Returns complete code snippet with:
    - Generated code
    - Setup instructions
    - File extension
    - Language information
    """
    try:
        generator = CodeGenerator()

        # Use company's first API key for the example
        # In production, you might want to fetch the actual key or generate a placeholder
        api_key = "your-api-key-here"  # Placeholder

        snippet_data = generator.generate_snippet(
            language=request.language,
            api_key=api_key,
            base_url=request.base_url or "http://localhost:8000",
            schema_id=request.schema_id
        )

        return SnippetResponse(
            code=snippet_data["code"],
            language=snippet_data["language"],
            language_name=snippet_data["language_name"],
            instructions=snippet_data["instructions"],
            file_extension=generator.get_snippet_file_extension(request.language)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate snippet: {str(e)}"
        )


@router.get(
    "/snippets",
    response_model=AllSnippetsResponse,
    summary="Generate all code snippets"
)
async def generate_all_snippets(
    company: CurrentCompanyEither,
    base_url: Optional[str] = "http://localhost:8000",
    schema_id: Optional[str] = None
):
    """
    Generate code snippets for all supported languages

    Convenient endpoint to get integration code for all available
    languages at once.

    ## Parameters

    - **base_url**: API base URL (default: http://localhost:8000)
    - **schema_id**: Optional schema ID to use in examples

    ## Response

    Returns map of language identifiers to complete snippet data
    for all supported languages.

    ## Use Cases

    - Show all integration options in documentation
    - Allow users to download multiple examples
    - Generate SDK documentation
    """
    try:
        generator = CodeGenerator()
        api_key = "your-api-key-here"  # Placeholder

        all_snippets = generator.generate_all_snippets(
            api_key=api_key,
            base_url=base_url,
            schema_id=schema_id
        )

        # Convert to response format
        response_snippets = {}
        for lang, data in all_snippets.items():
            response_snippets[lang] = SnippetResponse(
                code=data["code"],
                language=data["language"],
                language_name=data["language_name"],
                instructions=data["instructions"],
                file_extension=generator.get_snippet_file_extension(lang)
            )

        return AllSnippetsResponse(snippets=response_snippets)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate snippets: {str(e)}"
        )


@router.get(
    "/example/{language}",
    response_model=SnippetResponse,
    summary="Get example for specific language (convenience endpoint)"
)
async def get_language_example(
    language: str,
    company: CurrentCompanyEither,
    base_url: Optional[str] = "http://localhost:8000"
):
    """
    Get integration example for a specific language

    Convenience endpoint that's equivalent to POST /snippet but uses
    GET with path parameter.

    ## Parameters

    - **language**: Language identifier (python_flask, nodejs_express, etc.)
    - **base_url**: API base URL

    ## Response

    Returns code snippet for the specified language
    """
    request = SnippetRequest(
        language=language,
        base_url=base_url
    )

    return await generate_snippet(request, company)
