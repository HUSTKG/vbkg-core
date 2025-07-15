import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class CustomPythonExecutor(BaseStepExecutor):
    """Enhanced Custom Python executor với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            code = self.config.get("code", "")
            input_mapping = self.config.get("input_mapping", {})
            output_mapping = self.config.get("output_mapping", {})
            safe_mode = self.config.get("safe_mode", True)
            timeout_seconds = self.config.get("timeout_seconds", 30)

            if not code:
                raise PipelineExecutionError(
                    "No code provided for custom Python execution"
                )

            # Prepare execution environment with graph state
            execution_env = self._prepare_execution_environment(
                input_data, input_mapping
            )

            # Execute code safely
            execution_result = await self._execute_code_safely(
                code, execution_env, safe_mode, timeout_seconds
            )

            # Map output
            mapped_output = self._map_output(execution_result, output_mapping)

            return {
                "custom_result": self._track_provenance(
                    {
                        "execution_result": execution_result,
                        "mapped_output": mapped_output,
                        "execution_success": execution_result.get("success", False),
                        "execution_time": execution_result.get("execution_time", 0),
                    }
                ),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "custom_python",
                    "safe_mode": safe_mode,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Custom Python execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state từ custom Python results"""
        if "custom_result" in step_result:
            custom_data = step_result["custom_result"]
            if "data" in custom_data:
                mapped_output = custom_data["data"].get("mapped_output")

                # Check if output contains entities or relationships
                if isinstance(mapped_output, dict):
                    if "entities" in mapped_output:
                        entities = mapped_output["entities"]
                        if isinstance(entities, list):
                            self.graph_state.add_entities(entities, self.step_name)

                    if "relationships" in mapped_output:
                        relationships = mapped_output["relationships"]
                        if isinstance(relationships, list):
                            self.graph_state.add_relationships(
                                relationships, self.step_name
                            )

    def _prepare_execution_environment(
        self, input_data: Dict[str, Any], input_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare the execution environment with input data và graph state"""
        env = {
            "input_data": input_data,
            "graph_state": self.graph_state,
            "entities": self._get_best_entities(),
            "relationships": self._get_best_relationships(),
            "text_data": self._get_best_text_data(),
            "datetime": datetime,
            "json": json,
            "re": re,
            "logger": logger,
        }

        # Apply input mapping
        for var_name, data_path in input_mapping.items():
            try:
                # Simple dot notation path resolution
                value = input_data
                for key in data_path.split("."):
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
                env[var_name] = value
            except Exception as e:
                logger.warning(f"Error mapping input {var_name} from {data_path}: {e}")
                env[var_name] = None

        return env

    async def _execute_code_safely(
        self, code: str, env: Dict[str, Any], safe_mode: bool, timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute Python code safely with restrictions"""
        if safe_mode:
            # Check for dangerous operations
            dangerous_patterns = [
                r"import\s+os",
                r"import\s+sys",
                r"import\s+subprocess",
                r"__import__",
                r"eval\s*\(",
                r"exec\s*\(",
                r"open\s*\(",
                r"file\s*\(",
                r"input\s*\(",
                r"raw_input\s*\(",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    return {
                        "success": False,
                        "error": f"Dangerous operation detected: {pattern}",
                        "output": None,
                        "execution_time": 0,
                    }

        # Prepare safe execution environment
        safe_env = {
            **env,
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "range": range,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "enumerate": enumerate,
                "zip": zip,
                "all": all,
                "any": any,
                "print": print,
            },
        }

        try:
            start_time = datetime.now()

            # Create a namespace for execution
            local_env = {}

            # Execute the code
            exec(code, safe_env, local_env)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Extract result (look for 'result' variable or return the local environment)
            if "result" in local_env:
                output = local_env["result"]
            else:
                # Return all variables created in local scope
                output = {k: v for k, v in local_env.items() if not k.startswith("_")}

            return {
                "success": True,
                "output": output,
                "execution_time": execution_time,
                "local_variables": list(local_env.keys()),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None,
                "execution_time": 0,
            }

    def _map_output(
        self, execution_result: Dict[str, Any], output_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Map execution output according to output mapping configuration"""
        if not output_mapping or not execution_result.get("success"):
            return execution_result.get("output")

        mapped_output = {}
        output_data = execution_result.get("output", {})

        for output_key, source_path in output_mapping.items():
            try:
                # Simple dot notation path resolution
                value = output_data
                for key in source_path.split("."):
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
                mapped_output[output_key] = value
            except Exception as e:
                logger.warning(
                    f"Error mapping output {output_key} from {source_path}: {e}"
                )
                mapped_output[output_key] = None

        return mapped_output

