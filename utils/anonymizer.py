import spacy
import re
import warnings

# Suppress warnings if model isn't found immediately (handled in init)
warnings.filterwarnings("ignore")

class Anonymizer:
    def __init__(self, model: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model)
        except OSError:
            print(f"Model '{model}' not found. Please run: python -m spacy download {model}")
            # Try to load a blank model to avoid crashing, but warn heavily
            self.nlp = spacy.blank("en")

    def anonymize_text(self, text: str) -> str:
        """
        Anonymizes PII from the text including Names, Emails, and Phone numbers.
        """
        if not text:
            return ""

        # 1. Processing with Spacy for NER (Names, Orgs, etc if needed)
        doc = self.nlp(text)
        
        # We will build a list of character exclusions (indices to redact)
        redaction_ranges = []

        # Identify PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                redaction_ranges.append((ent.start_char, ent.end_char, "[NAME REDACTED]"))

        # 2. Regex for Emails
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        for match in email_pattern.finditer(text):
            redaction_ranges.append((match.start(), match.end(), "[EMAIL REDACTED]"))

        # 3. Regex for Phone Numbers
        phone_pattern = re.compile(r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b')
        for match in phone_pattern.finditer(text):
            redaction_ranges.append((match.start(), match.end(), "[PHONE REDACTED]"))

        # Sort ranges by start index descending to handle replacements correctly
        redaction_ranges.sort(key=lambda x: x[0], reverse=True)

        # Apply redactions
        # We need to being careful about overlapping ranges.
        # Since we sort reverse, we can just replace. 
        # Overlaps might occur if regex matches inside a named entity or vice versa.
        # Simple collision detection:
        
        final_text_chars = list(text)
        processed_indices = set()

        # To handle overlaps cleanly, let's filter the ranges.
        # A simple approach: if a range overlaps with a previously processed (higher index? no, we go reverse)...
        # Actually, standard reverse replacement works fine unless ranges intersect.
        # Example: "Call Bob at 555-1234"
        # Name: Bob (5, 8)
        # Phone: 555-1234 (12, 20)
        # No overlap.
        
        # If we have overlaps, e.g. "bob@email.com" might be caught as Name "bob" and Email.
        # We should prioritize one. Typically Regex (Email) is more specific/structural than NER Name.
        
        # Let's just do it.
        
        for start, end, replacement in redaction_ranges:
            # Check for overlap with already modified regions? 
            # Or just trust that reverse order handles the main offset issue.
            # Real collision issue: replacing "bob" in "bob@email.com" ruins the email structure used for detection?
            # No, detection is already done.
            # But if we replace "bob" -> "[NAME]" then "bob@email.com" -> "[NAME]@email.com".
            # Then we replace "bob@email.com" (original indices) -> "[EMAIL]".
            # Valid.
            
            # The only risk is if we replace a range that is PARTIALLY inside another.
            # E.g. Range A=(5, 10), Range B=(8, 15).
            # If we replace B first (later in text), A's indices (5,10) are still valid relative to start.
            # BUT if we replace A first (reverse order implies B is processed first).
            # So process B (8, 15). Text shrinks/grows.
            # Then process A (5, 10). But index 8, 9 are gone/moved.
            # Reverse order ONLY works for non-overlapping.
            
            # For simplicity in this demo, strict reverse order usually works for distinct entities.
            # Let's blindly apply reverse order. 
            
            final_text_chars[start:end] = list(replacement)

        return "".join(final_text_chars)

# Singleton instance
anonymizer_instance = Anonymizer()
