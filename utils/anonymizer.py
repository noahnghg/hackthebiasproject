import spacy
import re
import hashlib
import random
from typing import Optional
from parser import ResumeData


class ResumeAnonymizer:
    """Anonymize personal information in resume data"""
    
    def __init__(self, spacy_model="en_core_web_sm"):
        """Initialize anonymizer with spaCy model"""
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Model '{spacy_model}' not found. Run: python -m spacy download {spacy_model}")
            raise
        
        # Gender-indicating words to detect and anonymize
        self.gender_indicators = {
            'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself',
            'mr', 'mrs', 'ms', 'miss', 'mr.', 'mrs.', 'ms.',
            'male', 'female', 'man', 'woman', 'gentleman', 'lady'
        }
    
    def generate_candidate_id(self, name: str = None, email: str = None) -> str:
        """Generate a unique anonymous ID for the candidate"""
        if name or email:
            identifier = f"{name or ''}{email or ''}"
            # Create hash for anonymity
            hash_obj = hashlib.sha256(identifier.encode())
            hash_hex = hash_obj.hexdigest()[:12]
            return f"CANDIDATE-{hash_hex.upper()}"
        else:
            # Generate random ID
            random_id = ''.join(random.choices('0123456789ABCDEF', k=12))
            return f"CANDIDATE-{random_id}"
    
    def anonymize_text(self, text: str) -> str:
        """Remove or replace personal information from text"""
        if not text:
            return text
        
        doc = self.nlp(text)
        anonymized = text
        
        # Replace person names with [REDACTED]
        for ent in reversed(doc.ents):  # Reverse to maintain positions
            if ent.label_ == "PERSON":
                anonymized = (
                    anonymized[:ent.start_char] + 
                    "[REDACTED]" + 
                    anonymized[ent.end_char:]
                )
        
        # Remove gender indicators
        words = anonymized.split()
        anonymized_words = []
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if word_lower not in self.gender_indicators:
                anonymized_words.append(word)
            else:
                anonymized_words.append('[REDACTED]')
        
        return ' '.join(anonymized_words)
    
    def anonymize_location(self, location: str) -> Optional[str]:
        """Generalize location to city/state level only"""
        if not location:
            return None
        
        # Remove street addresses, zip codes
        # Keep only city and state
        location = re.sub(r'\d{5}(-\d{4})?', '', location)  # Remove ZIP
        location = re.sub(
            r'\d+\s+\w+\s+(street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)',
            '',
            location,
            flags=re.IGNORECASE
        )
        
        return location.strip()
    
    def anonymize(self, resume: ResumeData) -> ResumeData:
        """Anonymize all personal information in resume data
        
        Args:
            resume: ResumeData object to anonymize
            
        Returns:
            Anonymized ResumeData object
        """
        # Generate anonymous candidate ID
        resume.candidate_id = self.generate_candidate_id(resume.name, resume.email)
        
        # Remove direct identifiers
        resume.name = None
        resume.email = None
        resume.phone = None
        
        # Generalize location (keep city/state, remove address)
        if resume.location:
            resume.location = self.anonymize_location(resume.location)
        
        # Anonymize summary text
        if resume.summary:
            resume.summary = self.anonymize_text(resume.summary)
        
        # Anonymize experience descriptions
        for exp in resume.experience:
            if 'responsibilities' in exp:
                exp['responsibilities'] = [
                    self.anonymize_text(resp) for resp in exp['responsibilities']
                ]
        
        # Mark as anonymized
        resume.anonymized = True
        
        return resume