def display_message(message, limit=100):
    """Display the 100 first characters of a message
    """
    if len(message) <= limit:
        return message

    return message[: limit - 3].strip() + "..."
