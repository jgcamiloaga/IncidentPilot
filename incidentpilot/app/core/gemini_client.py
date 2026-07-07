import os
import json
import logging
from typing import Type
import requests
from pydantic import BaseModel
from dotenv import load_dotenv

# Bootstrap environment configurations
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Client wrapper for interacting with the Google Gemini API.
    
    Handles initialization of either the official Google GenAI SDK client or falling back 
    to direct HTTP REST requests if the SDK is unavailable or encounters configuration issues.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY environment variable not found. Please set it.")
        
        # Verify SDK availability and initialize client; fallback to REST if import fails
        self.use_sdk = False
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.use_sdk = True
            logger.info("Successfully initialized Gemini SDK client.")
        except Exception as e:
            logger.info(f"Using direct REST fallback. (SDK initialization skipped: {e})")

    def generate_json(self, prompt: str, schema_class: Type[BaseModel]) -> dict:
        """
        Submits a prompt to Gemini requesting a schema-conforming JSON response.
        Utilizes a model fallback chain to recover from 429 Rate Limit/Quota errors.

        Args:
            prompt (str): The prompt detailing instructions for the LLM.
            schema_class (Type[BaseModel]): Pydantic model class representing the target schema.

        Returns:
            dict: Deserialized JSON matching the structure of the schema_class.
        
        Raises:
            ValueError: If the API key is not configured.
            Exception: If request/deserialization fails for all models in the chain.
        """
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be configured to execute LLM calls.")

        # Failover model chain to bypass model-specific rate limits
        model_chain = [
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemma-4-26b-a4b-it"
        ]

        schema_json = schema_class.model_json_schema()
        schema_str = json.dumps(schema_json)
        schema_fields = json.dumps(schema_json, indent=2)
        system_instruction = (
            f"You are a helpful assistant. You must output valid JSON conforming strictly to "
            f"this JSON schema:\n{schema_fields}\nDo not include any markdown block markers like ```json."
        )

        full_prompt = f"{system_instruction}\n\nUser request:\n{prompt}"
        
        last_exception = None
        for model_name in model_chain:
            logger.info(f"Attempting JSON generation with model: {model_name}")
            
            # Attempt to request via official Google GenAI SDK if successfully loaded
            if self.use_sdk:
                try:
                    from google.genai import types
                    
                    # Omit response_schema if the Pydantic schema contains unsupported features (like arbitrary dicts generating additionalProperties)
                    use_response_schema = schema_class if "additionalProperties" not in schema_str else None
                    
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=use_response_schema,
                            temperature=0.1,
                        )
                    )
                    if response.text:
                        clean_text = self._clean_json_response(response.text)
                        return json.loads(clean_text)
                except Exception as e:
                    err_msg = str(e).lower()
                    # If it's a rate limit or quota error, skip directly to the next model in the chain
                    if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                        logger.warning(f"Model {model_name} rate limit exceeded: {e}. Trying next model in chain...")
                        last_exception = e
                        continue
                    else:
                        logger.warning(f"GenAI SDK call failed for {model_name}: {e}. Falling back to REST API for this model...")
            
            # Fallback to direct HTTP REST request for the current model
            try:
                return self._generate_json_rest(full_prompt, model_name)
            except Exception as e:
                err_msg = str(e).lower()
                logger.warning(f"REST API call failed for model {model_name}: {e}")
                last_exception = e
                # Continue loop to try next model in the chain
                continue
                
        raise Exception(f"All models in the fallback chain exhausted. Last error: {last_exception}")

    def _generate_json_rest(self, prompt: str, model_name: str) -> dict:
        """
        Executes a direct POST request to the Gemini API endpoint.
        
        Args:
            prompt (str): Prepared payload containing instructions and schema injection.
            model_name (str): The target model string.

        Returns:
            dict: Parsed JSON response candidates.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Gemini API request failed with status {response.status_code}: {response.text}")
            
        data = response.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            clean_text = self._clean_json_response(text)
            return json.loads(clean_text)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to parse JSON response from REST API. Response: {data}. Error: {e}")

    def _clean_json_response(self, text: str) -> str:
        """
        Removes typical markdown block decorators (e.g. ```json) and surrounding whitespaces.
        
        Args:
            text (str): Raw response output from LLM.

        Returns:
            str: Normalized JSON string.
        """
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
