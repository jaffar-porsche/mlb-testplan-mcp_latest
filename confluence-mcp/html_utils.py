"""HTML sanitization utilities for Confluence storage format."""
import re


def sanitize_html_for_confluence(html_content):
    """
    Sanitize HTML content to be compatible with Confluence storage format.
    """
    if not html_content:
        return html_content

    content = str(html_content)

    # Replace self-closing br tags with proper XHTML format
    content = re.sub(r'<br\s*/?>', '<br />', content)

    # Replace self-closing img tags with proper XHTML format
    content = re.sub(r'<img([^>]*?)/?>', r'<img\1 />', content)

    # Replace self-closing hr tags with proper XHTML format
    content = re.sub(r'<hr\s*/?>', '<hr />', content)

    # Replace self-closing input tags with proper XHTML format
    content = re.sub(r'<input([^>]*?)/?>', r'<input\1 />', content)

    # If content doesn't look like proper HTML, wrap it in a paragraph
    if not content.strip().startswith('<') or not content.strip().endswith('>'):
        content = f'<p>{content}</p>'

    return content
