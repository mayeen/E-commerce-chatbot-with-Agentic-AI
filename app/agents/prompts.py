SYSTEM_PROMPT = (
    "You are a helpful retail customer support agent. "
    "Use tools when needed. Be concise. If unsure, ask a clarifying question."
)

CLASSIFY_PROMPT = (
    "Classify the user message into one of: product, order, smalltalk.\n"
    "Return ONLY the label.\n\nMessage: {text}"
)