# response_model.py
# Simplified schema compatible with the generative models endpoint
response_model_schema = {
    "type": "OBJECT",
    "properties": {
        "overall_rating": {
            "type": "STRING",
            "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
        },
        "summary": {"type": "STRING"},
        "issues": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {
                        "type": "STRING",
                        "enum": ["bug", "style", "performance", "security", "maintainability"]
                    },
                    "severity": {
                        "type": "STRING",
                        "enum": ["high", "medium", "low"]
                    },
                    # allow integer OR null using type ARRAY
                    "line": {
                        "type": ["INTEGER", "NULL"]
                    },
                    "message": {"type": "STRING"},
                    "suggestion": {"type": "STRING"}
                },
                "required": ["type", "severity", "message"]
            }
        },
        "positive_feedback": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    },
    "required": ["overall_rating", "summary", "issues", "positive_feedback"]
   
}
