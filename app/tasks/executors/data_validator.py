import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.tasks.executors.base import PipelineExecutionError

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class DataValidatorExecutor(BaseStepExecutor):
    """Enhanced Data validator với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Data validation cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for validation")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validation_rules = self.config.get("validation_rules", {})
            schema_validation = validation_rules.get("schema_validation", True)
            quality_checks = validation_rules.get("quality_checks", True)
            business_rules = validation_rules.get("business_rules", [])
            required_fields = validation_rules.get("required_fields", [])

            # Use best text data từ graph state
            data_to_validate = self._get_best_text_data()

            validation_results = {
                "is_valid": True,
                "validation_errors": [],
                "quality_score": 0.0,
                "field_completeness": {},
                "business_rule_violations": [],
            }

            total_items = len(data_to_validate)
            if total_items == 0:
                validation_results["quality_score"] = 1.0
                return {
                    "validation_results": self._track_provenance(validation_results),
                    "validated_data": data_to_validate,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "data_validator",
                    },
                }

            valid_items = 0
            field_counts = {}

            for item in data_to_validate:
                item_valid = True

                if schema_validation:
                    schema_errors = self._validate_item_schema(item, required_fields)
                    if schema_errors:
                        validation_results["validation_errors"].extend(schema_errors)
                        item_valid = False

                if quality_checks:
                    quality_issues = self._check_item_quality(item)
                    if quality_issues:
                        validation_results["validation_errors"].extend(quality_issues)
                        item_valid = False

                for rule in business_rules:
                    violations = self._check_business_rule(item, rule)
                    if violations:
                        validation_results["business_rule_violations"].extend(
                            violations
                        )
                        item_valid = False

                # Track field completeness
                if isinstance(item, dict):
                    for field in required_fields:
                        if field in field_counts:
                            field_counts[field] += 1
                        else:
                            field_counts[field] = 1

                        if field in item and item[field]:
                            if f"{field}_filled" in field_counts:
                                field_counts[f"{field}_filled"] += 1
                            else:
                                field_counts[f"{field}_filled"] = 1

                if item_valid:
                    valid_items += 1

            validation_results["quality_score"] = (
                valid_items / total_items if total_items > 0 else 1.0
            )
            validation_results["is_valid"] = (
                len(validation_results["validation_errors"]) == 0
            )

            # Calculate field completeness
            for field in required_fields:
                total_field = field_counts.get(field, 0)
                filled_field = field_counts.get(f"{field}_filled", 0)
                validation_results["field_completeness"][field] = {
                    "total": total_field,
                    "filled": filled_field,
                    "completeness_rate": (
                        filled_field / total_field if total_field > 0 else 0.0
                    ),
                }

            return {
                "validation_results": self._track_provenance(validation_results),
                "validated_data": data_to_validate,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "data_validator",
                    "total_items_validated": total_items,
                    "valid_items": valid_items,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Data validator execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với validation results"""
        if "validation_results" in step_result:
            validation_data = step_result["validation_results"]
            if isinstance(validation_data, dict) and "data" in validation_data:
                self.graph_state.set_validation_results(
                    validation_data["data"], self.step_name
                )

    def _validate_item_schema(
        self, item: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate item against schema requirements"""
        errors = []

        if not isinstance(item, dict):
            errors.append(f"Item is not a dictionary: {type(item)}")
            return errors

        for field in required_fields:
            if field not in item:
                errors.append(f"Missing required field: {field}")
            elif not item[field]:
                errors.append(f"Empty value for required field: {field}")

        return errors

    def _check_item_quality(self, item: Dict[str, Any]) -> List[str]:
        """Check quality of item data"""
        issues = []

        if isinstance(item, dict):
            for key in ["content", "text", "entity_text"]:
                if key in item and isinstance(item[key], str):
                    if len(item[key].strip()) < 3:
                        issues.append(f"Suspiciously short {key}: '{item[key]}'")

            placeholder_values = ["TODO", "TBD", "N/A", "null", "undefined", ""]
            for key, value in item.items():
                if str(value).strip() in placeholder_values:
                    issues.append(f"Placeholder value in {key}: '{value}'")

            if "confidence" in item:
                try:
                    confidence = float(item["confidence"])
                    if not (0.0 <= confidence <= 1.0):
                        issues.append(f"Confidence score out of range: {confidence}")
                except (ValueError, TypeError):
                    issues.append(
                        f"Invalid confidence score type: {type(item['confidence'])}"
                    )

        return issues

    def _check_business_rule(
        self, item: Dict[str, Any], rule: Dict[str, Any]
    ) -> List[str]:
        """Check business rule against item"""
        violations = []

        rule_type = rule.get("type")
        if rule_type == "min_length":
            field = rule.get("field")
            min_length = rule.get("value", 0)
            if field in item and isinstance(item[field], str):
                if len(item[field]) < min_length:
                    violations.append(
                        f"Field {field} below minimum length {min_length}"
                    )

        elif rule_type == "regex_match":
            field = rule.get("field")
            pattern = rule.get("pattern")
            if field in item and isinstance(item[field], str):
                if not re.match(pattern, item[field]):
                    violations.append(f"Field {field} does not match pattern {pattern}")

        elif rule_type == "allowed_values":
            field = rule.get("field")
            allowed_values = rule.get("values", [])
            if field in item and item[field] not in allowed_values:
                violations.append(f"Field {field} has disallowed value: {item[field]}")

        return violations


