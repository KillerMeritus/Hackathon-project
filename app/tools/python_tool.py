"""
Python execution tool - safely executes Python code
"""
import sys
import io
import traceback
from typing import Any, Dict

from .base import BaseTool
from ..core.exceptions import ToolExecutionError


class PythonTool(BaseTool):
    """Tool for executing Python code safely"""

    @property
    def name(self) -> str:
        return "python"

    @property
    def description(self) -> str:
        return "Execute Python code and return the output. Useful for calculations, data processing, and analysis."

    async def execute(self, input_data: Any, **kwargs) -> str:
        """
        Execute Python code and capture output

        Args:
            input_data: Python code as a string

        Returns:
            Captured stdout/stderr output or result
        """
        code = str(input_data)

        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = io.StringIO()
        redirected_error = io.StringIO()

        try:
            sys.stdout = redirected_output
            sys.stderr = redirected_error

            # Create a restricted globals dict
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "bool": bool,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "any": any,
                    "all": all,
                    "isinstance": isinstance,
                    "type": type,
                }
            }

            # Execute the code
            exec(code, safe_globals)

            # Get output
            output = redirected_output.getvalue()
            error = redirected_error.getvalue()

            if error:
                return f"Output:\n{output}\n\nErrors:\n{error}"

            return output if output else "Code executed successfully (no output)"

        except Exception as e:
            error_trace = traceback.format_exc()
            raise ToolExecutionError("python", f"Execution failed:\n{error_trace}")

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }