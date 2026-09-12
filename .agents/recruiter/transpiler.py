#!/usr/bin/env python3
"""
Claude-to-Gemini Skill & Tool Schema Transpiler for Strategist.
Transpiles Claude XML tags and Anthropic tool definitions into Gemini-native FunctionDeclarations.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

XML_TAG_PATTERNS = [
    re.compile(r"<thinking>.*?</thinking>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<claude_execution>.*?</claude_execution>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<function_calls>.*?</function_calls>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<antml:.*?>.*?</antml:.*?>", re.DOTALL | re.IGNORECASE),
]

TYPE_MAPPING = {
    "string": "genai.protos.Type.STRING",
    "integer": "genai.protos.Type.INTEGER",
    "number": "genai.protos.Type.NUMBER",
    "boolean": "genai.protos.Type.BOOLEAN",
    "array": "genai.protos.Type.ARRAY",
    "object": "genai.protos.Type.OBJECT",
}


def strip_claude_xml(text: str) -> str:
    """Strip Anthropic-specific XML wrappers from prompts and skills."""
    cleaned = text
    for pattern in XML_TAG_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    # Also clean loose tags
    cleaned = re.sub(r"</?(?:thinking|claude_execution|function_calls|antml:[^>]+)>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def transpile_schema_to_gemini_code(tool_def: Dict[str, Any], indent_level: int = 0) -> str:
    """
    Transpile an Anthropic tool schema definition to Gemini Python FunctionDeclaration code.
    Example:
      execute_query_declaration = genai.protos.FunctionDeclaration(
          name="execute_query",
          description="Run SQL query on internal DB",
          parameters=genai.protos.Schema(...)
      )
    """
    name = tool_def.get("name", "unnamed_tool")
    desc = tool_def.get("description", "")
    params = tool_def.get("parameters", {})

    code_lines = [
        f"{name}_declaration = genai.protos.FunctionDeclaration(",
        f'    name="{name}",',
        f'    description="{desc}",',
    ]

    def render_schema_obj(schema_dict: Dict[str, Any], indent: int) -> List[str]:
        pad = " " * indent
        stype = schema_dict.get("type", "object")
        gemini_type = TYPE_MAPPING.get(stype, "genai.protos.Type.OBJECT")
        lines = [f"{pad}genai.protos.Schema("]
        lines.append(f"{pad}    type={gemini_type},")

        if "description" in schema_dict:
            lines.append(f'{pad}    description="{schema_dict["description"]}",')

        props = schema_dict.get("properties", {})
        if props:
            lines.append(f"{pad}    properties={{")
            for prop_name, prop_val in props.items():
                lines.append(f'{pad}        "{prop_name}": ')
                sub_lines = render_schema_obj(prop_val, indent + 8)
                lines[-1] += sub_lines[0].lstrip()
                lines.extend(sub_lines[1:])
                lines[-1] += ","
            lines.append(f"{pad}    }},")

        req = schema_dict.get("required", [])
        if req:
            req_str = json.dumps(req)
            lines.append(f"{pad}    required={req_str}")

        lines.append(f"{pad})")
        return lines

    if params:
        schema_lines = render_schema_obj(params, 4)
        code_lines.append(f"    parameters={schema_lines[0].lstrip()}")
        code_lines.extend(schema_lines[1:])
    code_lines.append(")")

    return "\n".join(code_lines)


def transpile_tool_dict_to_gemini_json(tool_def: Dict[str, Any]) -> Dict[str, Any]:
    """Transpile tool dictionary to clean Gemini-compatible JSON schema."""
    cleaned_desc = strip_claude_xml(tool_def.get("description", ""))
    return {
        "name": tool_def.get("name"),
        "description": cleaned_desc,
        "parameters": tool_def.get("parameters", {"type": "object", "properties": {}})
    }


def run_self_test() -> bool:
    """Self-test transpilation with the prompt example."""
    sample_claude_tool = {
        "name": "execute_query",
        "description": "Run SQL query on internal DB <thinking>internal only</thinking>",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The raw SQL statement"}
            },
            "required": ["query"]
        }
    }

    # 1. XML Stripping
    sample_text = "Before <thinking>Do not expose</thinking> After"
    cleaned = strip_claude_xml(sample_text)
    assert cleaned == "Before  After", f"XML strip failed: {cleaned}"

    # 2. Python Code Generation
    py_code = transpile_schema_to_gemini_code(sample_claude_tool)
    assert "execute_query_declaration = genai.protos.FunctionDeclaration" in py_code
    assert "genai.protos.Type.STRING" in py_code

    # 3. Gemini JSON Schema Generation
    gemini_json = transpile_tool_dict_to_gemini_json(sample_claude_tool)
    assert gemini_json["description"] == "Run SQL query on internal DB"
    assert "query" in gemini_json["parameters"]["properties"]

    print("Transpiler self-test passed successfully.")
    return True


if __name__ == "__main__":
    if "--test" in sys.argv or len(sys.argv) == 1:
        run_self_test()
