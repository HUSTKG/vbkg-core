import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

from app.tasks.executors.base import PipelineExecutionError

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class DataCleanerExecutor(BaseStepExecutor):
    """Enhanced Data cleaner với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Data cleaning cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for cleaning")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cleaning_rules = self.config.get("cleaning_rules", {})
            remove_duplicates = cleaning_rules.get("remove_duplicates", True)
            normalize_text = cleaning_rules.get("normalize_text", True)
            remove_empty = cleaning_rules.get("remove_empty", True)
            custom_rules = cleaning_rules.get("custom_rules", [])

            # Use best text data từ graph state
            data_to_clean = self._get_best_text_data()

            cleaning_stats = {
                "original_count": len(data_to_clean),
                "duplicates_removed": 0,
                "empty_values_removed": 0,
                "normalization_applied": 0,
                "custom_rules_applied": 0,
            }

            cleaned_data = []

            # Step 1: Remove duplicates
            if remove_duplicates:
                seen = set()
                for item in data_to_clean:
                    item_key = self._generate_item_key(item)
                    if item_key not in seen:
                        seen.add(item_key)
                        cleaned_data.append(item)
                    else:
                        cleaning_stats["duplicates_removed"] += 1
                data_to_clean = cleaned_data

            # Step 2: Remove empty values
            if remove_empty:
                original_count = len(data_to_clean)
                data_to_clean = [
                    item for item in data_to_clean if self._is_not_empty(item)
                ]
                cleaning_stats["empty_values_removed"] = original_count - len(
                    data_to_clean
                )

            # Step 3: Normalize text
            if normalize_text:
                for item in data_to_clean:
                    if self._normalize_item_text(item):
                        cleaning_stats["normalization_applied"] += 1

            # Step 4: Apply custom rules
            for rule in custom_rules:
                rule_type = rule.get("type")
                if rule_type == "regex_replace":
                    pattern = rule.get("pattern")
                    replacement = rule.get("replacement", "")
                    for item in data_to_clean:
                        if self._apply_regex_rule(item, pattern, replacement):
                            cleaning_stats["custom_rules_applied"] += 1

                elif rule_type == "value_mapping":
                    mapping = rule.get("mapping", {})
                    for item in data_to_clean:
                        if self._apply_value_mapping(item, mapping):
                            cleaning_stats["custom_rules_applied"] += 1

            cleaning_stats["final_count"] = len(data_to_clean)

            return {
                "cleaned_data": self._track_provenance(data_to_clean),
                "cleaning_stats": cleaning_stats,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "data_cleaner",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Data cleaner execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với cleaned data"""
        if "cleaned_data" in step_result:
            cleaned = step_result["cleaned_data"]
            if isinstance(cleaned, dict) and "data" in cleaned:
                cleaned_items = cleaned["data"]
                if isinstance(cleaned_items, list):
                    self.graph_state.set_cleaned_data(cleaned_items, self.step_name)

    def _generate_item_key(self, item: Dict[str, Any]) -> str:
        """Generate a unique key for duplicate detection"""
        if isinstance(item, dict):
            content = item.get("content") or item.get("text") or str(item)
            return str(
                hash(
                    content.strip().lower()
                    if isinstance(content, str)
                    else str(content)
                )
            )
        return hash(str(item))

    def _is_not_empty(self, item: Dict[str, Any]) -> bool:
        """Check if item is not empty"""
        if not item:
            return False

        if isinstance(item, dict):
            content = item.get("content") or item.get("text")
            if content:
                return bool(str(content).strip())
            return any(v for v in item.values() if v)

        return bool(str(item).strip())

    def _normalize_item_text(self, item: Dict[str, Any]) -> bool:
        """Normalize text content in item"""
        normalized = False

        if isinstance(item, dict):
            for key in ["content", "text", "entity_text"]:
                if key in item and isinstance(item[key], str):
                    original = item[key]
                    normalized_text = re.sub(r"\s+", " ", original.strip())
                    normalized_text = re.sub(
                        r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", "", normalized_text
                    )

                    if normalized_text != original:
                        item[key] = normalized_text
                        normalized = True

        return normalized

    def _apply_regex_rule(
        self, item: Dict[str, Any], pattern: str, replacement: str
    ) -> bool:
        """Apply regex replacement rule"""
        applied = False

        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    new_value = re.sub(pattern, replacement, value)
                    if new_value != value:
                        item[key] = new_value
                        applied = True

        return applied

    def _apply_value_mapping(
        self, item: Dict[str, Any], mapping: Dict[str, str]
    ) -> bool:
        """Apply value mapping rule"""
        applied = False

        if isinstance(item, dict):
            for key, value in item.items():
                if str(value) in mapping:
                    item[key] = mapping[str(value)]
                    applied = True

        return applied
