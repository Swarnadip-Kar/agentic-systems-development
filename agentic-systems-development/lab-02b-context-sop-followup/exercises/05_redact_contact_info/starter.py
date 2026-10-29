import re

def redact_contact_info(text: str) -> str:
    # Regular expression patterns for email addresses and phone numbers
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(?:\+\d{1,3}\s?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    
    # Replace email addresses with '[REDACTED]'
    redacted_text = re.sub(email_pattern, '[REDACTED]', text)
    
    # Replace phone numbers with '[REDACTED]'
    redacted_text = re.sub(phone_pattern, '[REDACTED]', redacted_text)
    
    return redacted_text

# Example usage:
# print(redact_contact_info("Contact me at example@example.com or call (123) 456-7890"))
