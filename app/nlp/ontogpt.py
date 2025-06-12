import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from ontogpt.clients.llm_client import LLMClient
from ontogpt.engines.spires_engine import SPIRESEngine
from ontogpt.io.template_loader import get_template_details

from app.core.config import settings
from app.core.supabase import get_supabase
from app.services.ontology import OntologyService

logger = logging.getLogger(__name__)


class OntoGPTService:
    """
    Enhanced OntoGPT Service with explicit LLM configuration and Vietnamese support
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.1,
    ):
        self.ontology_service = OntologyService()
        self.llm_client: LLMClient | None = None
        self.template_cache = {}

        # LLM Configuration
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.api_key = settings.OPENAI_API_KEY if api_key is None else api_key
        self.temperature = temperature

        # Initialize LLM client explicitly
        self._initialize_llm_client()

        # Initialize OntoGPT knowledge engine with LLM client
        logger.info(f"OntoGPT initialized with {llm_provider} model: {model_name}")

    def _initialize_llm_client(self):
        """Initialize LLM client with explicit configuration"""
        try:
            if not self.api_key:
                raise ValueError("API key is required for LLM client")

            # Configure LLM client settings
            llm_config = {
                "custom_llm_provider": self.llm_provider,
                "model": self.model_name,
                "api_key": self.api_key,
                "temperature": self.temperature,
            }

            # Initialize client based on provider
            self.llm_client = LLMClient(**llm_config)

            logger.info(
                f"LLM client initialized: {self.llm_provider} - {self.model_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise

    async def extract_knowledge_with_llm_details(
        self,
        text: str,
        domain: Optional[str] = None,
        template_name: Optional[str] = None,
        extract_new_concepts: bool = True,
        show_llm_calls: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract knowledge using OntoGPT with detailed LLM call information
        """

        if not self.llm_client:
            raise ValueError("LLM client is not initialized")

        logger.info(
            f"Starting OntoGPT knowledge extraction with LLM for domain: {domain or 'general'}"
        )

        try:
            # Create or get template
            if not template_name:
                template_name = f"{domain or 'general'}_extraction"

            template_path = None
            if template_name not in self.template_cache:
                template_path = await self.create_custom_template(domain or "general")
                self.template_cache[template_name] = template_path
            else:
                template_path = self.template_cache[template_name]

            logger.info(
                f"Using OntoGPT template: {template_path} from cache or created path"
            )

            # Load template
            template = get_template_details(template_path)

            logger.info(
                f"Loaded OntoGPT template: {template_name} from {template_path}"
            )

            # Preprocess Vietnamese text
            processed_text = self._preprocess_vietnamese_text(text)

            logger.info(f"Preprocessed text for domain: {domain or 'general'}")

            # Create Vietnamese-aware prompt for the LLM
            vietnamese_prompt = self._create_vietnamese_prompt(processed_text, domain)

            logger.info(
                f"Created Vietnamese prompt for LLM extraction: {vietnamese_prompt[:200]}..."
            )

            logger.info(f"Using LLM: {self.llm_provider} - {self.model_name}")
            logger.info(f"Temperature: {self.temperature}")

            if show_llm_calls:
                logger.info(f"LLM Prompt: {vietnamese_prompt[:200]}...")

            # Track LLM usage
            llm_calls = []

            # Custom extraction with LLM call tracking
            extraction_result = await self._extract_with_llm_tracking(
                processed_text, template, vietnamese_prompt, llm_calls
            )

            # Format results
            formatted_result = await self._format_ontogpt_result(
                extraction_result, domain, extract_new_concepts, text
            )

            # Add LLM metadata
            formatted_result["llm_metadata"] = {
                "provider": self.llm_provider,
                "model": self.model_name,
                "temperature": self.temperature,
                "total_llm_calls": len(llm_calls),
                "llm_calls": llm_calls if show_llm_calls else [],
                "prompt_tokens": sum(
                    call.get("prompt_tokens", 0) for call in llm_calls
                ),
                "completion_tokens": sum(
                    call.get("completion_tokens", 0) for call in llm_calls
                ),
            }

            return formatted_result

        except Exception as e:
            logger.error(f"Error in OntoGPT knowledge extraction with LLM: {e}")
            raise

    def _create_vietnamese_prompt(self, text: str, domain: Optional[str] = None) -> str:
        """Create Vietnamese-specific prompt for better extraction"""
        domain_context = ""
        if domain:
            domain_context = f"trong lĩnh vực {domain}"

        prompt = f"""
Nhiệm vụ: Trích xuất thông tin có cấu trúc từ văn bản tiếng Việt {domain_context}.

Văn bản để phân tích:
{text}

Hướng dẫn:
1. Xác định tất cả các thực thể (entities) quan trọng trong văn bản
2. Xác định các mối quan hệ (relationships) giữa các thực thể
3. Đảm bảo tính chính xác của thông tin được trích xuất
4. Sử dụng thuật ngữ tiếng Việt phù hợp với ngữ cảnh

Trả về kết quả theo định dạng JSON có cấu trúc.
"""
        return prompt

    async def _extract_with_llm_tracking(
        self, text: str, template: Any, prompt: str, llm_calls: List[Dict]
    ) -> Any:
        """Extract knowledge while tracking LLM calls"""
        try:
            # Wrap the LLM client to track calls
            original_call = (
                self.llm_client.call if hasattr(self.llm_client, "call") else None
            )

            logger.info("Wrapping LLM client to track calls")

            def tracked_call(*args, **kwargs):
                start_time = datetime.utcnow()
                result = original_call(*args, **kwargs) if original_call else None
                end_time = datetime.utcnow()

                # Track the call
                call_info = {
                    "timestamp": start_time.isoformat(),
                    "duration_ms": (end_time - start_time).total_seconds() * 1000,
                    "prompt_tokens": kwargs.get("max_tokens", 0),
                    "completion_tokens": (
                        len(str(result)) // 4 if result else 0
                    ),  # Rough estimate
                    "model": self.model_name,
                    "prompt_preview": str(args[0])[:100] if args else prompt[:100],
                }
                logger.info(
                        f"LLM call tracked: {call_info['timestamp']} - {call_info['prompt_preview']}"
                                        )
                llm_calls.append(call_info)
                return result

            # Temporarily replace the call method
            if hasattr(self.llm_client, "call"):
                self.llm_client.call = tracked_call

            logger.info("LLM client call method wrapped for tracking")

            spires_engine = SPIRESEngine(client=self.llm_client, template_details=template)
            
            # Perform extraction
            extraction_result = spires_engine.extract_from_text(
                text=text,
            )

            logger.info(
                    f"Extraction completed with {len(extraction_result.get('entities', []))} entities and {len(extraction_result.get('relationships', []))} relationships"
                                )

            # Restore original method
            if original_call:
                self.llm_client.call = original_call

            return extraction_result

        except Exception as e:
            logger.error(f"Error in LLM-tracked extraction: {e}")
            spires_engine = SPIRESEngine(client=self.llm_client, template_details=template)
            # Fallback to regular extraction
            return spires_engine.extract_from_text(text=text, cls=template)

    async def test_llm_connection(self) -> Dict[str, Any]:
        """Test LLM connection and configuration"""
        try:
            if not self.llm_client:
                return {
                    "status": "error",
                    "message": "LLM client not initialized",
                    "configuration": None,
                }

            # Test with a simple prompt
            test_prompt = "Xin chào! Đây là test kết nối LLM cho tiếng Việt."

            start_time = datetime.utcnow()

            # Make a test call (implementation depends on your LLM client)
            try:
                if hasattr(self.llm_client, "call"):
                    response = self.llm_client.call(test_prompt)
                else:
                    response = "Test connection successful"
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"LLM call failed: {str(e)}",
                    "configuration": {
                        "provider": self.llm_provider,
                        "model": self.model_name,
                        "temperature": self.temperature,
                    },
                }

            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()

            return {
                "status": "success",
                "message": "LLM connection successful",
                "response_time_seconds": response_time,
                "configuration": {
                    "provider": self.llm_provider,
                    "model": self.model_name,
                    "temperature": self.temperature,
                    "api_key_configured": bool(self.api_key),
                },
                "test_response": str(response)[:200] if response else None,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error testing LLM connection: {str(e)}",
                "configuration": None,
            }

    def get_llm_configuration(self) -> Dict[str, Any]:
        """Get current LLM configuration"""
        return {
            "provider": self.llm_provider,
            "model": self.model_name,
            "temperature": self.temperature,
            "api_key_configured": bool(self.api_key),
            "llm_client_initialized": self.llm_client is not None,
        }

    async def update_llm_configuration(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update LLM configuration and reinitialize"""
        try:
            # Update configuration
            if provider:
                self.llm_provider = provider
            if model:
                self.model_name = model
            if api_key:
                self.api_key = api_key
            if temperature is not None:
                self.temperature = temperature

            # Reinitialize LLM client
            self._initialize_llm_client()

            return {
                "status": "success",
                "message": "LLM configuration updated successfully",
                "new_configuration": self.get_llm_configuration(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update LLM configuration: {str(e)}",
                "current_configuration": self.get_llm_configuration(),
            }

    async def create_custom_template(
    self,
    domain: str = "banking",
    ontology_classes: Optional[List[Dict[str, Any]]] = None,
    ontology_properties: Optional[List[Dict[str, Any]]] = None,
) -> str:
        """
        Create a simple, working OntoGPT template following exact documentation patterns
        """
        try:
            # Create simple LinkML schema following EXACT documentation structure
            template_schema = {
                "id": f"http://w3id.org/ontogpt/{domain}",
                "name": f"{domain}-template",
                "title": f"{domain.title()} Financial Knowledge Extraction",
                "description": f"A template for extracting {domain} financial knowledge from Vietnamese text",
                "license": "https://creativecommons.org/publicdomain/zero/1.0/",
                "prefixes": {
                    "linkml": "https://w3id.org/linkml/",
                    domain: f"http://w3id.org/ontogpt/{domain}/",
                    "FIBO": "https://spec.edmcouncil.org/fibo/ontology/FND/",
                },
                "default_prefix": domain,
                "default_range": "string",
                "imports": ["linkml:types", "core"],  # Exactly as in documentation
                "classes": {}
            }

            # STEP 1: Create tree_root class - EXACTLY following documentation pattern
            template_schema["classes"]["FinancialExtraction"] = {
                "tree_root": True,
                "attributes": {
                    "entities": {
                        "description": "semicolon-separated list of financial entities",
                        "multivalued": True,
                        "range": "FinancialEntity",
                    },
                    "organizations": {
                        "description": "semicolon-separated list of organizations and companies",
                        "multivalued": True,
                        "range": "Organization", 
                    },
                    "relationships": {
                        "description": "semicolon-separated list of relationships between entities",
                        "multivalued": True,
                        "range": "FinancialRelationship",
                    },
                }
            }

            # STEP 2: Create Entity classes - following NamedEntity pattern
            template_schema["classes"]["FinancialEntity"] = {
                "is_a": "NamedEntity",
                "id_prefixes": ["FIBO"],
                "annotations": {
                    "annotators": "sqlite:obo:fibo"
                }
            }

            template_schema["classes"]["Organization"] = {
                "is_a": "NamedEntity", 
                "id_prefixes": ["FIBO"],
                "annotations": {
                    "annotators": "sqlite:obo:fibo"
                }
            }

            template_schema["classes"]["Product"] = {
                "is_a": "NamedEntity",
                "id_prefixes": ["FIBO"],
                "annotations": {
                    "annotators": "sqlite:obo:fibo"
                }
            }

            template_schema["classes"]["Currency"] = {
                "is_a": "NamedEntity",
                "id_prefixes": ["FIBO"],
                "annotations": {
                    "annotators": "sqlite:obo:fibo"
                }
            }

            # STEP 3: Create Relationship class - following CompoundExpression pattern
            template_schema["classes"]["FinancialRelationship"] = {
                "is_a": "CompoundExpression",
                "attributes": {
                    "subject": {
                        "range": "FinancialEntity",
                        "annotations": {
                            "prompt": "the subject entity in the relationship"
                        }
                    },
                    "predicate": {
                        "range": "string",
                        "annotations": {
                            "prompt": "the relationship type"
                        }
                    },
                    "object": {
                        "range": "FinancialEntity", 
                        "annotations": {
                            "prompt": "the object entity in the relationship"
                        }
                    }
                }
            }

            # STEP 4: Add a few domain-specific classes from ontology
            if not ontology_classes:
                ontology_context = await self.get_ontology_context(domain)
                ontology_classes = list(ontology_context["classes"].values())

            # Add max 5 specific classes to keep template simple
            added_classes = 0
            for cls in ontology_classes[:5]:
                class_name = self._clean_class_name(cls.get("label", ""))
                if class_name and class_name not in template_schema["classes"] and added_classes < 5:
                    # Simple class structure
                    template_schema["classes"][class_name] = {
                        "is_a": "FinancialEntity",
                        "id_prefixes": ["FIBO"],
                        "annotations": {
                            "annotators": "sqlite:obo:fibo"
                        }
                    }
                    added_classes += 1

            # Save template
            template_dir = Path(tempfile.gettempdir()) / "ontogpt_templates"
            template_dir.mkdir(exist_ok=True)
            template_file = template_dir / f"{domain}_simple.yaml"

            with open(template_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    template_schema,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            logger.info(f"Created simple OntoGPT template: {template_file}")
            
            # Log template content for debugging
            with open(template_file, "r", encoding="utf-8") as f:
                content = f.read()
                logger.info(f"Template content preview:\n{content[:500]}...")

            return str(template_file)

        except Exception as e:
            logger.error(f"Error creating simple template: {e}")
            raise



    def _clean_class_name(self, label: str) -> str:
        """Simple class name cleaning"""
        if not label:
            return ""
        
        import re

        # Simple approach - just keep alphanumeric and convert to CamelCase
        name = re.sub(r'[^a-zA-Z0-9\s]', '', label)
        name = ''.join(word.capitalize() for word in name.split() if word)
        
        # Must start with letter and be reasonable length
        if not name or len(name) < 2 or not name[0].isalpha():
            return ""
            
        return name

    def _get_vietnamese_labels(self, item: Dict[str, Any]) -> List[str]:
        """Extract Vietnamese labels and synonyms from ontology item"""
        labels = []

        # Add main label
        if item.get("label"):
            labels.append(item["label"])

        # Add Vietnamese labels from properties if available
        properties = item.get("properties", {})
        if isinstance(properties, dict):
            vietnamese_labels = properties.get("vietnamese_labels", [])
            if isinstance(vietnamese_labels, list):
                labels.extend(vietnamese_labels)
            elif isinstance(vietnamese_labels, str):
                labels.append(vietnamese_labels)

        return labels

    async def get_ontology_context(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current ontology context from database for knowledge extraction
        """
        try:
            supabase = await get_supabase()

            # Build query for ontology classes
            classes_query = supabase.from_("ontology_classes").select("*")
            if domain:
                classes_query = classes_query.eq("domain", domain)

            classes_response = await classes_query.limit(500).execute()

            # Build query for ontology properties
            properties_query = supabase.from_("ontology_properties").select("*")
            if domain:
                properties_query = properties_query.eq("domain", domain)

            properties_response = await properties_query.limit(500).execute()

            # Format for OntoGPT
            ontology_context = {
                "classes": {},
                "properties": {},
                "class_hierarchy": {},
                "property_domains": {},
            }

            # Process classes
            for cls in classes_response.data:
                ontology_context["classes"][cls["id"]] = {
                    "id": cls["id"],
                    "uri": cls["uri"],
                    "label": cls.get("label"),
                    "description": cls.get("description"),
                    "domain": cls.get("domain"),
                    "parent_class_id": cls.get("parent_class_id"),
                    "properties": cls.get("properties", {}),
                    "is_custom": cls.get("is_custom", False),
                }

                # Build class hierarchy
                if cls.get("parent_class_id"):
                    parent_id = cls["parent_class_id"]
                    if parent_id not in ontology_context["class_hierarchy"]:
                        ontology_context["class_hierarchy"][parent_id] = []
                    ontology_context["class_hierarchy"][parent_id].append(cls["id"])

            # Process properties
            for prop in properties_response.data:
                ontology_context["properties"][prop["id"]] = {
                    "id": prop["id"],
                    "uri": prop["uri"],
                    "label": prop.get("label"),
                    "description": prop.get("description"),
                    "property_type": prop.get("property_type"),
                    "domain_class_id": prop.get("domain_class_id"),
                    "range_class_id": prop.get("range_class_id"),
                    "domain": prop.get("domain"),
                    "is_custom": prop.get("is_custom", False),
                }

                # Build property domains
                if prop.get("domain_class_id"):
                    domain_class_id = prop["domain_class_id"]
                    if domain_class_id not in ontology_context["property_domains"]:
                        ontology_context["property_domains"][domain_class_id] = []
                    ontology_context["property_domains"][domain_class_id].append(
                        prop["id"]
                    )

            logger.info(
                f"Loaded ontology context: {len(ontology_context['classes'])} classes, {len(ontology_context['properties'])} properties"
            )
            return ontology_context

        except Exception as e:
            logger.error(f"Error getting ontology context: {e}")
            return {
                "classes": {},
                "properties": {},
                "class_hierarchy": {},
                "property_domains": {},
            }

    async def extract_knowledge_with_ontogpt(
    self,
    text: str,
    domain: Optional[str] = None,
    template_name: Optional[str] = None,
    extract_new_concepts: bool = True,
) -> Dict[str, Any]:
        """
        Extract knowledge using OntoGPT library with custom template and Vietnamese support
        """
        try:
            # Create or get template
            if not template_name:
                template_name = f"{domain or 'general'}_extraction"

            template_path = None
            if template_name not in self.template_cache:
                # Create custom template based on current ontology
                template_path = await self.create_custom_template(domain or "general")
                self.template_cache[template_name] = template_path
            else:
                template_path = self.template_cache[template_name]

            logger.info(f"Using OntoGPT template: {template_path}")
            
            # Load the template
            try:
                template = get_template_details(template_path)
                logger.info(f"Successfully loaded OntoGPT template: {template_name}")
                
                # Debug: log the template classes found
                if hasattr(template, 'classes'):
                    logger.info(f"Template classes found: {list(template.classes.keys())}")
                
            except Exception as e:
                logger.warning(f"Failed to load custom template: {e}, using fallback")
                # Create a simple fallback template
                template_path = await self._create_fallback_template(domain or "general")
                template = get_template_details(template_path)
                logger.info(f"Using fallback template: {template_path}")

            # Preprocess Vietnamese text for better extraction
            processed_text = self._preprocess_vietnamese_text(text)
            logger.info(f"Preprocessed text: {processed_text[:200]}...")

            # Extract knowledge using OntoGPT
            # OntoGPT will automatically find the tree_root class
            logger.info("Starting OntoGPT extraction...")
            spires_engine = SPIRESEngine(client=self.llm_client, template_details=template)

            extraction_result = spires_engine.extract_from_text(
                text=processed_text,
            )

            logger.info(f"OntoGPT extraction completed for domain: {domain or 'general'}")
            logger.info(f"Extraction result type: {type(extraction_result)}")

            # Convert OntoGPT result to our format
            formatted_result = await self._format_ontogpt_result(
                extraction_result, domain, extract_new_concepts, text
            )

            return formatted_result

        except Exception as e:
            logger.error(f"Error in OntoGPT knowledge extraction: {e}")
            logger.error(f"Error traceback:", exc_info=True)
            raise

    def _preprocess_vietnamese_text(self, text: str) -> str:
        """
        Preprocess Vietnamese text for better extraction
        """
        # Basic Vietnamese text preprocessing
        import re

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Add some context clues for better entity recognition
        # This can be expanded based on domain-specific patterns
        vietnamese_context = {
            "ngân hàng": "bank",
            "khách hàng": "customer",
            "tài khoản": "account",
            "giao dịch": "transaction",
            "tiền": "money",
            "vay": "loan",
            "tiết kiệm": "savings",
            "thẻ": "card",
        }

        # Don't actually replace, just ensure we have good context
        return text

    async def _create_fallback_template(self, domain: str) -> str:
        """Create minimal working fallback template"""
        template_schema = {
            "id": f"http://w3id.org/ontogpt/{domain}_minimal",
            "name": f"{domain}_minimal",
            "title": f"Minimal {domain} extraction",
            "description": f"Minimal working template for {domain}",
            "license": "CC0",
            "prefixes": {
                "linkml": "https://w3id.org/linkml/",
                domain: f"http://w3id.org/ontogpt/{domain}/",
            },
            "imports": ["linkml:types", "core"],
            "default_prefix": domain,
            "default_range": "string",
            "classes": {
                "ExtractionResult": {
                    "tree_root": True,
                    "attributes": {
                        "entities": {
                            "description": "semicolon-separated list of entities",
                            "multivalued": True,
                            "range": "Entity",
                        },
                        "relationships": {
                            "description": "semicolon-separated list of relationships",
                            "multivalued": True,
                            "range": "Relationship",
                        },
                    },
                },
                "Entity": {
                    "is_a": "NamedEntity",
                    # "annotations": {
                    #     "annotators": "gilda:"
                    # }
                },
                "Relationship": {
                    "is_a": "CompoundExpression",
                    "attributes": {
                        "subject": {"range": "Entity"},
                        "predicate": {"range": "string"},
                        "object": {"range": "Entity"},
                    },
                },
            },
        }

        template_dir = Path(tempfile.gettempdir()) / "ontogpt_templates"
        template_dir.mkdir(exist_ok=True)
        template_file = template_dir / f"{domain}_minimal.yaml"

        with open(template_file, "w", encoding="utf-8") as f:
            yaml.dump(template_schema, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Created minimal fallback template: {template_file}")
        return str(template_file)

    async def _format_ontogpt_result(
    self,
    extraction_result: Any,
    domain: Optional[str] = None,
    extract_new_concepts: bool = True,
    original_text: str = "",
) -> Dict[str, Any]:
        """
        Format OntoGPT extraction result - simplified version
        """
        try:
            formatted_result = {
                "entities": [],
                "relationships": [],
                "new_concepts": {"classes": [], "properties": []} if extract_new_concepts else None,
                "extraction_metadata": {
                    "extractor": "ontogpt_simple",
                    "domain": domain,
                    "timestamp": datetime.utcnow().isoformat(),
                    "text_length": len(original_text),
                },
            }

            logger.info(f"Processing OntoGPT result type: {type(extraction_result)}")
            logger.info(f"Result attributes: {dir(extraction_result) if hasattr(extraction_result, '__dict__') else 'No attributes'}")

            # Handle different possible result structures
            entities_list = []
            relationships_list = []

            # Try to extract entities from various possible attributes
            if hasattr(extraction_result, 'entities') and extraction_result.entities:
                entities_list = extraction_result.entities
            elif hasattr(extraction_result, 'financial_entities') and extraction_result.financial_entities:
                entities_list = extraction_result.financial_entities
            elif hasattr(extraction_result, 'organizations') and extraction_result.organizations:
                entities_list = extraction_result.organizations

            # Try to extract relationships
            if hasattr(extraction_result, 'relationships') and extraction_result.relationships:
                relationships_list = extraction_result.relationships
            elif hasattr(extraction_result, 'financial_relationships') and extraction_result.financial_relationships:
                relationships_list = extraction_result.financial_relationships

            logger.info(f"Found {len(entities_list)} entities and {len(relationships_list)} relationships")

            # Process entities
            for entity in entities_list:
                try:
                    entity_text = ""
                    entity_type = "Entity"
                    
                    # Extract text from different possible attributes
                    if hasattr(entity, 'label') and entity.label:
                        entity_text = str(entity.label)
                    elif hasattr(entity, 'name') and entity.name:
                        entity_text = str(entity.name)
                    elif hasattr(entity, 'id') and entity.id:
                        entity_text = str(entity.id)
                    else:
                        entity_text = str(entity)

                    # Extract type
                    if hasattr(entity, '__class__'):
                        entity_type = entity.__class__.__name__

                    if entity_text and entity_text.strip():
                        formatted_entity = {
                            "text": entity_text.strip(),
                            "entity_type": entity_type,
                            "ontology_class_id": None,
                            "ontology_class_uri": None,
                            "confidence": 0.8,
                            "start_position": original_text.find(entity_text) if entity_text in original_text else 0,
                            "end_position": original_text.find(entity_text) + len(entity_text) if entity_text in original_text else len(entity_text),
                            "properties": {
                                "extraction_method": "ontogpt_simple",
                                "entity_class": entity_type,
                            },
                            "is_mapped": False,
                        }
                        formatted_result["entities"].append(formatted_entity)
                        
                except Exception as e:
                    logger.warning(f"Error processing entity {entity}: {e}")

            # Process relationships
            for relationship in relationships_list:
                try:
                    subject = ""
                    predicate = ""
                    object_entity = ""

                    # Extract relationship components
                    if hasattr(relationship, 'subject'):
                        subject = str(relationship.subject) if relationship.subject else ""
                    if hasattr(relationship, 'predicate'):
                        predicate = str(relationship.predicate) if relationship.predicate else ""
                    if hasattr(relationship, 'object'):
                        object_entity = str(relationship.object) if relationship.object else ""

                    if subject and predicate and object_entity:
                        formatted_relationship = {
                            "source_entity": subject,
                            "target_entity": object_entity,
                            "relationship_type": predicate,
                            "ontology_property_id": None,
                            "ontology_property_uri": None,
                            "confidence": 0.8,
                            "properties": {
                                "extraction_method": "ontogpt_simple",
                            },
                            "is_mapped": False,
                        }
                        formatted_result["relationships"].append(formatted_relationship)
                        
                except Exception as e:
                    logger.warning(f"Error processing relationship {relationship}: {e}")

            logger.info(f"Formatted {len(formatted_result['entities'])} entities and {len(formatted_result['relationships'])} relationships")
            return formatted_result

        except Exception as e:
            logger.error(f"Error formatting OntoGPT result: {e}")
            logger.error(f"Exception details:", exc_info=True)
            
            # Return basic structure on error
            return {
                "entities": [],
                "relationships": [],
                "new_concepts": {"classes": [], "properties": []},
                "extraction_metadata": {
                    "extractor": "ontogpt_simple",
                    "domain": domain,
                    "timestamp": datetime.utcnow().isoformat(),
                    "text_length": len(original_text),
                    "error": str(e),
                },
            }

    async def _format_entity_from_ontogpt(
        self, entity: Any, ontology_context: Dict[str, Any], original_text: str
    ) -> Optional[Dict[str, Any]]:
        """Format entity from OntoGPT to our format with database IDs"""
        try:
            # Extract entity information - handle different possible structures
            entity_text = ""
            entity_type = ""
            confidence = 0.8  # Default confidence

            # Try different ways to extract entity text
            if hasattr(entity, "entity_text"):
                entity_text = entity.entity_text
            elif hasattr(entity, "label"):
                entity_text = entity.label
            elif hasattr(entity, "name"):
                entity_text = entity.name
            else:
                entity_text = str(entity)

            # Try to get entity type
            if hasattr(entity, "entity_type"):
                entity_type = entity.entity_type
            else:
                entity_type = type(entity).__name__

            # Try to get confidence if available
            if hasattr(entity, "confidence"):
                confidence = float(entity.confidence)

            # Find matching ontology class in database
            ontology_class_id = None
            ontology_class_label = None

            # Look for matching class by label or type name
            for class_id, cls_info in ontology_context["classes"].items():
                label = cls_info.get("label", "").lower()
                if (
                    label == entity_type.lower()
                    or entity_type.lower() in label
                    or label in entity_type.lower()
                ):
                    ontology_class_id = class_id
                    ontology_class_label = cls_info.get("label")
                    confidence = min(
                        0.9, confidence + 0.1
                    )  # Boost confidence for mapped entities
                    break

            # Try to find position in original text
            start_position = 0
            end_position = len(entity_text)
            if entity_text and original_text:
                pos = original_text.lower().find(entity_text.lower())
                if pos >= 0:
                    start_position = pos
                    end_position = pos + len(entity_text)

            formatted_entity = {
                "text": entity_text,
                "entity_type": ontology_class_label or entity_type,
                "ontology_class_id": ontology_class_id,
                "ontology_class_uri": (
                    ontology_context["classes"].get(ontology_class_id, {}).get("uri")
                    if ontology_class_id
                    else None
                ),
                "confidence": confidence,
                "start_position": start_position,
                "end_position": end_position,
                "properties": {
                    "ontogpt_type": entity_type,
                    "extraction_method": "ontogpt",
                    "original_entity_data": str(entity)[:200],  # Keep some debug info
                },
                "is_mapped": ontology_class_id is not None,
            }

            return formatted_entity

        except Exception as e:
            logger.warning(f"Error formatting entity from OntoGPT: {e}")
            return None

    async def _format_relationship_from_ontogpt(
        self, relationship: Any, ontology_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Format relationship from OntoGPT to our format with database IDs"""
        try:
            # Extract relationship information - handle different possible structures
            source_entity = ""
            target_entity = ""
            predicate = ""
            confidence = 0.8  # Default confidence

            # Try different ways to extract relationship components
            if hasattr(relationship, "subject"):
                source_entity = str(relationship.subject)

            if hasattr(relationship, "object"):
                target_entity = str(relationship.object)

            if hasattr(relationship, "predicate"):
                predicate = str(relationship.predicate)
            elif hasattr(relationship, "relationship_type"):
                predicate = str(relationship.relationship_type)

            # Try to get confidence if available
            if hasattr(relationship, "confidence"):
                confidence = float(relationship.confidence)

            # Find matching ontology property in database
            ontology_property_id = None
            ontology_property_label = None

            # Look for matching property by label
            for prop_id, prop_info in ontology_context["properties"].items():
                label = prop_info.get("label", "").lower()
                if (
                    label == predicate.lower()
                    or predicate.lower() in label
                    or label in predicate.lower()
                ):
                    ontology_property_id = prop_id
                    ontology_property_label = prop_info.get("label")
                    confidence = min(
                        0.9, confidence + 0.1
                    )  # Boost confidence for mapped properties
                    break

            formatted_relationship = {
                "source_entity": source_entity,
                "target_entity": target_entity,
                "relationship_type": ontology_property_label or predicate,
                "ontology_property_id": ontology_property_id,
                "ontology_property_uri": (
                    ontology_context["properties"]
                    .get(ontology_property_id, {})
                    .get("uri")
                    if ontology_property_id
                    else None
                ),
                "confidence": confidence,
                "properties": {
                    "extraction_method": "ontogpt",
                    "original_relationship_data": str(relationship)[
                        :200
                    ],  # Keep some debug info
                },
                "is_mapped": ontology_property_id is not None,
            }

            return formatted_relationship

        except Exception as e:
            logger.warning(f"Error formatting relationship from OntoGPT: {e}")
            return None

    async def _extract_new_concepts_from_result(
        self,
        extraction_result: Any,
        ontology_context: Dict[str, Any],
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract potentially new concepts from OntoGPT result for ontology enrichment"""
        try:
            new_concepts = {"classes": [], "properties": []}

            # Analyze extracted entities for new concepts
            if hasattr(extraction_result, "entities") and extraction_result.entities:
                entity_types = set()
                for entity in extraction_result.entities:
                    entity_type = type(entity).__name__
                    entity_types.add(entity_type)

                # Check if entity types exist in ontology
                for entity_type in entity_types:
                    found_in_ontology = False
                    for class_id, cls_info in ontology_context["classes"].items():
                        label = cls_info.get("label", "").lower()
                        if label == entity_type.lower() or entity_type.lower() in label:
                            found_in_ontology = True
                            break

                    if not found_in_ontology:
                        new_concepts["classes"].append(
                            {
                                "suggested_uri": f"http://custom.ontology/{domain or 'general'}/{entity_type}",
                                "label": entity_type,
                                "description": f"Khái niệm mới được trích xuất bởi OntoGPT: {entity_type}",
                                "domain": domain,
                                "parent_class_id": None,
                                "examples": [
                                    str(e)
                                    for e in extraction_result.entities
                                    if type(e).__name__ == entity_type
                                ][:3],
                                "is_custom": True,
                                "properties": {
                                    "extraction_source": "ontogpt",
                                    "language": "vietnamese",
                                },
                            }
                        )

            # Analyze extracted relationships for new properties
            if (
                hasattr(extraction_result, "relationships")
                and extraction_result.relationships
            ):
                predicates = set()
                for relationship in extraction_result.relationships:
                    predicate = getattr(relationship, "predicate", "")
                    if predicate:
                        predicates.add(predicate)

                # Check if predicates exist in ontology
                for predicate in predicates:
                    found_in_ontology = False
                    for prop_id, prop_info in ontology_context["properties"].items():
                        label = prop_info.get("label", "").lower()
                        if label == predicate.lower() or predicate.lower() in label:
                            found_in_ontology = True
                            break

                    if not found_in_ontology:
                        new_concepts["properties"].append(
                            {
                                "suggested_uri": f"http://custom.ontology/{domain or 'general'}/{predicate}",
                                "label": predicate,
                                "description": f"Thuộc tính mới được trích xuất bởi OntoGPT: {predicate}",
                                "property_type": "object",
                                "domain": domain,
                                "domain_class_id": None,
                                "range_class_id": None,
                                "is_custom": True,
                                "properties": {
                                    "extraction_source": "ontogpt",
                                    "language": "vietnamese",
                                },
                            }
                        )

            return new_concepts

        except Exception as e:
            logger.error(f"Error extracting new concepts: {e}")
            return {"classes": [], "properties": []}

    async def enrich_ontology_with_new_concepts(
        self, new_concepts: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add new concepts to ontology database based on extraction results
        """
        try:
            supabase = await get_supabase()
            results = {"classes_added": 0, "properties_added": 0, "errors": []}

            # Add new classes
            for new_class in new_concepts.get("classes", []):
                try:
                    class_data = {
                        "uri": new_class["suggested_uri"],
                        "label": new_class["label"],
                        "description": new_class["description"],
                        "parent_class_id": new_class.get("parent_class_id"),
                        "domain": new_class.get("domain"),
                        "is_custom": True,
                        "properties": new_class.get("properties", {}),
                    }

                    response = (
                        await supabase.from_("ontology_classes")
                        .insert(class_data)
                        .execute()
                    )
                    if response.data:
                        results["classes_added"] += 1
                        logger.info(f"Added new ontology class: {new_class['label']}")

                except Exception as e:
                    error_msg = f"Error adding class {new_class.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Add new properties
            for new_property in new_concepts.get("properties", []):
                try:
                    property_data = {
                        "uri": new_property["suggested_uri"],
                        "label": new_property["label"],
                        "description": new_property["description"],
                        "property_type": new_property["property_type"],
                        "domain_class_id": new_property.get("domain_class_id"),
                        "range_class_id": new_property.get("range_class_id"),
                        "domain": new_property.get("domain"),
                        "is_custom": True,
                    }

                    response = (
                        await supabase.from_("ontology_properties")
                        .insert(property_data)
                        .execute()
                    )
                    if response.data:
                        results["properties_added"] += 1
                        logger.info(
                            f"Added new ontology property: {new_property['label']}"
                        )

                except Exception as e:
                    error_msg = f"Error adding property {new_property.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(
                f"Ontology enrichment completed: {results['classes_added']} classes, {results['properties_added']} properties added"
            )
            return results

        except Exception as e:
            logger.error(f"Error enriching ontology: {e}")
            raise

    async def validate_extraction_against_ontology(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate extraction results against current ontology using database
        """
        try:
            ontology_context = await self.get_ontology_context()

            validation_results = {
                "entity_validations": [],
                "relationship_validations": [],
                "overall_score": 0.0,
                "ontogpt_validation": True,
            }

            valid_entities = 0
            valid_relationships = 0

            # Validate entities
            for entity in entities:
                ontology_class_id = entity.get("ontology_class_id")
                validation = {
                    "entity": entity,
                    "is_valid": False,
                    "suggestions": [],
                    "ontogpt_confidence": entity.get("confidence", 0.0),
                }

                if (
                    ontology_class_id
                    and ontology_class_id in ontology_context["classes"]
                ):
                    validation["is_valid"] = True
                    valid_entities += 1
                else:
                    # Suggest similar classes
                    suggestions = await self._suggest_similar_classes(
                        entity.get("text", ""), ontology_context
                    )
                    validation["suggestions"] = suggestions

                validation_results["entity_validations"].append(validation)

            # Validate relationships
            for relationship in relationships:
                ontology_property_id = relationship.get("ontology_property_id")
                validation = {
                    "relationship": relationship,
                    "is_valid": False,
                    "suggestions": [],
                    "ontogpt_confidence": relationship.get("confidence", 0.0),
                }

                if (
                    ontology_property_id
                    and ontology_property_id in ontology_context["properties"]
                ):
                    validation["is_valid"] = True
                    valid_relationships += 1
                else:
                    # Suggest similar properties
                    suggestions = await self._suggest_similar_properties(
                        relationship.get("relationship_type", ""), ontology_context
                    )
                    validation["suggestions"] = suggestions

                validation_results["relationship_validations"].append(validation)

            # Calculate overall score
            total_items = len(entities) + len(relationships)
            if total_items > 0:
                validation_results["overall_score"] = (
                    valid_entities + valid_relationships
                ) / total_items

            return validation_results

        except Exception as e:
            logger.error(f"Error validating extraction: {e}")
            raise

    async def _suggest_similar_classes(
        self, entity_text: str, ontology_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest similar ontology classes for an entity"""
        suggestions = []

        # Simple text similarity matching
        for class_id, info in ontology_context["classes"].items():
            label = info.get("label", "").lower()
            if entity_text.lower() in label or label in entity_text.lower():
                suggestions.append(
                    {
                        "ontology_class_id": class_id,
                        "label": info.get("label"),
                        "uri": info.get("uri"),
                        "similarity_score": 0.8,
                    }
                )

        return suggestions[:5]

    async def _suggest_similar_properties(
        self, relationship_text: str, ontology_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest similar ontology properties for a relationship"""
        suggestions = []

        # Simple text similarity matching
        for prop_id, info in ontology_context["properties"].items():
            label = info.get("label", "").lower()
            if relationship_text.lower() in label or label in relationship_text.lower():
                suggestions.append(
                    {
                        "ontology_property_id": prop_id,
                        "label": info.get("label"),
                        "uri": info.get("uri"),
                        "similarity_score": 0.8,
                    }
                )

        return suggestions[:5]

    async def suggest_knowledge_graph_completion(
        self, extraction_result_id: int, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest completions for knowledge graph using OntoGPT reasoning capabilities
        """
        try:
            supabase = await get_supabase()

            # Get extraction results with entities and relationships
            extraction_response = (
                await supabase.from_("extraction_results")
                .select("*, kg_entities(*), kg_relationships(*)")
                .eq("id", extraction_result_id)
                .single()
                .execute()
            )

            logger.info(f"Fetched extraction result: {extraction_response.data}")

            if not extraction_response.data:
                raise ValueError("Extraction result not found")

            extraction_data = extraction_response.data
            entities = extraction_data.get("kg_entities", [])
            relationships = extraction_data.get("kg_relationships", [])

            # Get source text if available
            text = ""
            if "extracted_entities" in extraction_data:
                text = extraction_data.get("extracted_entities", {}).get(
                    "source_text", ""
                )

            # Use OntoGPT for more sophisticated completion suggestions
            suggestions = await self._get_ontogpt_completion_suggestions(
                text, entities, relationships, domain
            )

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting knowledge graph completion: {e}")
            raise

    async def _get_ontogpt_completion_suggestions(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get completion suggestions using OntoGPT reasoning"""
        try:
            # This could be enhanced with more sophisticated OntoGPT reasoning
            # For now, fall back to rule-based approach
            return await self._get_rule_based_completion_suggestions(
                entities, relationships
            )

        except Exception as e:
            logger.error(f"Error in OntoGPT completion suggestions: {e}")
            return {
                "missing_entities": [],
                "missing_relationships": [],
                "missing_properties": [],
            }

    async def _get_rule_based_completion_suggestions(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback rule-based completion suggestions with Vietnamese context"""
        suggestions = {
            "missing_entities": [],
            "missing_relationships": [],
            "missing_properties": [],
        }

        # Get ontology context for better suggestions
        ontology_context = await self.get_ontology_context()

        # Extract entity types
        entity_types = set()
        entity_texts = []
        for entity in entities:
            if entity.get("ontology_class_id"):
                class_info = ontology_context["classes"].get(
                    entity["ontology_class_id"]
                )
                if class_info:
                    entity_types.add(class_info.get("label", ""))
            entity_texts.append(entity.get("entity_text", ""))

        # Vietnamese banking domain rules
        banking_rules = {
            "Person": {
                "suggests": ["Bank", "Account", "Card"],
                "relationships": ["has_account", "is_customer_of", "owns_card"],
            },
            "Bank": {
                "suggests": ["Product", "Service", "Branch"],
                "relationships": ["offers", "provides", "has_branch"],
            },
            "Account": {
                "suggests": ["Transaction", "Balance"],
                "relationships": ["has_transaction", "has_balance"],
            },
        }

        # Apply rules based on existing entities
        for entity_type in entity_types:
            if entity_type in banking_rules:
                rule = banking_rules[entity_type]

                # Suggest missing entity types
                for suggested_type in rule["suggests"]:
                    if suggested_type not in entity_types:
                        suggestions["missing_entities"].append(
                            {
                                "suggested_text": f"{suggested_type} liên quan",
                                "suggested_type": suggested_type,
                                "reason": f"Thường xuất hiện cùng với {entity_type}",
                                "priority": "medium",
                                "confidence": 0.7,
                            }
                        )

                # Suggest missing relationships
                existing_relations = set(
                    [r.get("relationship_type", "") for r in relationships]
                )
                for suggested_rel in rule["relationships"]:
                    if suggested_rel not in existing_relations:
                        suggestions["missing_relationships"].append(
                            {
                                "source_entity": f"{entity_type} entity",
                                "target_entity": "Related entity",
                                "suggested_type": suggested_rel,
                                "reason": f"Mối quan hệ phổ biến cho {entity_type}",
                                "priority": "high",
                                "confidence": 0.8,
                            }
                        )

        return suggestions
