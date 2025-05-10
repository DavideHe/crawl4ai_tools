

PROMPT_EXTRACT_TEXT_WITH_INSTRUCTION = """Here is the URL of the webpage:
<url>{URL}</url>

And here is the cleaned HTML content of that webpage:
<html>
{HTML}
</html>

Your task is to break down this HTML content into text following the provided user's REQUEST.

This is the user's REQUEST, pay attention to it:
<request>
{REQUEST}
</request>
"""