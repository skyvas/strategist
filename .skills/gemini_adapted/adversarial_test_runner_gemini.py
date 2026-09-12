# Auto-transpiled for Google Gemini Runtime
import google.generativeai as genai

run_adversarial_qa_suite_declaration = genai.protos.FunctionDeclaration(
    name="run_adversarial_qa_suite",
    description="Executes Loop A adversarial test cases against warehouse ticket state transitions <thinking>Assert that transitions enforce blocker reason and validate operational metadata</thinking>",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "test_suite": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="Target test suite identifier (e.g. LoopA_WarehouseOps)",
            ),
            "fail_fast": genai.protos.Schema(
                type=genai.protos.Type.BOOLEAN,
                description="Stop on first assertion failure",
            ),
        },
        required=["test_suite"]
    )
)
