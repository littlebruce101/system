def route_request(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if any(word in prompt_lower for word in ["breathe","feel","overwhelm","comfort"]):
        return "cordelia"
    elif any(word in prompt_lower for word in ["map","branch","scenario","option","deadline"]):
        return "starhawk"
    elif "both" in prompt_lower:
        return "mediator"  # will sequence cordelia → starhawk
    else:
        return "mediator"