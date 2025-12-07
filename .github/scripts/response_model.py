# response_model.py
# Simplified schema compatible with the generative models endpoint
response_model_schema = {
    "type": "object",
    "properties": {
        "overall_rating": {
            "type": "string",
            "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
        },
        "summary": {"type": "string"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["bug", "style", "performance", "security", "maintainability"]
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    },
                    # allow integer OR null using type array
                    "line": {
                        "type": ["integer", "null"]
                    },
                    "message": {"type": "string"},
                    "suggestion": {"type": "string"}
                },
                "required": ["type", "severity", "message"]
            }
        },
        "positive_feedback": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["overall_rating", "summary", "issues", "positive_feedback"]
   
}
