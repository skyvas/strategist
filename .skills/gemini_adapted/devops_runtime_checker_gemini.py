# Auto-transpiled for Google Gemini Runtime
import google.generativeai as genai

audit_runtime_and_security_declaration = genai.protos.FunctionDeclaration(
    name="audit_runtime_and_security",
    description="Executes Loop B DevOps checks: linting, syntax validation, self-contained server execution, and responsive viewport checks <thinking>Reject code with hardcoded credentials or unhandled port collisions</thinking>",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "target_dir": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Target workspace directory for runtime inspection",
            ),
            "check_responsive": genai.protos.Schema(
                type=genai.protos.Type.BOOLEAN,
                description="Validate Samsung Tab A8 and mobile viewport CSS rules",
            ),
        },
        required=["target_dir"]
    )
)
