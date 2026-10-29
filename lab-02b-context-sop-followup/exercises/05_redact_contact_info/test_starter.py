import unittest
from starter import redact_contact_info

class TestRedactContactInfo(unittest.TestCase):
    def test_redact_email_addresses(self):
        self.assertEqual(redact_contact_info("Contact me at example@example.com"), "Contact me at [REDACTED]")
        self.assertEqual(redact_contact_info("Reach out to user.name+tag+sorting@example.com"), "Reach out to [REDACTED]")
        self.assertEqual(redact_contact_info("No email here"), "No email here")
        self.assertEqual(redact_contact_info("Multiple emails: test1@example.com and test2@domain.org"), "Multiple emails: [REDACTED] and [REDACTED]")

    def test_redact_phone_numbers(self):
        self.assertEqual(redact_contact_info("Call me at 123-456-7890"), "Call me at [REDACTED]")
        self.assertEqual(redact_contact_info("Call me at (123) 456-7890"), "Call me at [REDACTED]")
        self.assertEqual(redact_contact_info("Call me at 123.456.7890"), "Call me at [REDACTED]")
        self.assertEqual(redact_contact_info("Call me at 123 456 7890"), "Call me at [REDACTED]")
        self.assertEqual(redact_contact_info("Call me at 1234567823"), "Call me at [REDACTED]")
        self.assertEqual(redact_contact_info("Call me at +91 1234567819"), "Call me at [REDACTED]")
        self.assertEqual(redact_contact_info("No phone number here"), "No phone number here")
        self.assertEqual(redact_contact_info("Multiple phones: 123-456-7890 and (987) 654-3210"), "Multiple phones: [REDACTED] and [REDACTED]")

    def test_redact_mixed_content(self):
        self.assertEqual(redact_contact_info("Contact me at example@example.com or call 123-456-7890"), "Contact me at [REDACTED] or call [REDACTED]")
        self.assertEqual(redact_contact_info("Email: user@domain.com, Phone: (123) 456-7890"), "Email: [REDACTED], Phone: [REDACTED]")
        self.assertEqual(redact_contact_info("No contact info here"), "No contact info here")

    def test_empty_string(self):
        self.assertEqual(redact_contact_info(""), "")

    def test_no_matches(self):
        self.assertEqual(redact_contact_info("Just some random text"), "Just some random text")

if __name__ == '__main__':
    unittest.main()
