"""
Safe prompt template substitution.

str.format() breaks when prompt files contain JSON examples with {braces}.
This replaces only the known {PLACEHOLDER} keys we supply, leaving all
other curly braces (JSON syntax, examples) untouched.
"""


def fill_template(template: str, **kwargs) -> str:
    """Replace {key} for each key in kwargs. All other braces are left as-is."""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result
