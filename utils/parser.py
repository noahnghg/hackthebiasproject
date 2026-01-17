import pdfplumber
import spacy
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
import hashlib
import random

@dataclass
class ResumeData:
    """Data structure to hold parsed resume information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = None
    experience: List[Dict] = None
    education: List[Dict] = None
    anonymized: bool = False  # Track if data is anonymized
    candidate_id: Optional[str] = None  # Anonymous ID
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.experience is None:
            self.experience = []
        if self.education is None:
            self.education = []
    
    def to_dict(self):
        """Convert to dictionary for JSON export"""
        return asdict(self)
    
    def to_json(self, indent=2):
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class ResumeParser:
    """Parse resume PDFs and extract structured data"""
    
    def __init__(self,pdf_path: str,spacy_model="en_core_web_sm"):
        """Initialize parser with spaCy model"""
        if not pdf_path:
            raise ValueError("pdf_path must be provided")

        self.pdf_path = pdf_path
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Model '{spacy_model}' not found. Run: python -m spacy download {spacy_model}")
            raise
        
        # Common technical skills (expand this list)
        self.skills_database = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'node.js', 'express',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
            'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra', 'elasticsearch',
            'git', 'github', 'gitlab', 'jira', 'agile', 'scrum',
            'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'spacy', 'spark', 'hadoop', 'kafka'
        }
        
        # Gender-indicating words to detect and anonymize
        self.gender_indicators = {
            'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself',
            'mr', 'mrs', 'ms', 'miss', 'mr.', 'mrs.', 'ms.',
            'male', 'female', 'man', 'woman', 'gentleman', 'lady'
        }
        
        # Section headers to look for
        self.section_headers = {
            'experience': ['experience', 'work experience', 'employment', 'professional experience'],
            'education': ['education', 'academic background', 'qualification'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'summary': ['summary', 'profile', 'professional summary', 'about']
        }
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove bullets
        text = re.sub(r'[●•◆▪▸➤⦿✓✔]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address using regex"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        # Common formats: (123) 456-7890, 123-456-7890, 123.456.7890
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract name (usually first line or first PERSON entity)"""
        # Try first line (common in resumes)
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            # Check if it's a reasonable name (2-4 words, mostly letters)
            words = first_line.split()
            if 2 <= len(words) <= 4 and all(w.replace('.', '').isalpha() for w in words):
                return first_line
        
        # Fallback: use spaCy NER
        doc = self.nlp(text[:500])  # Check first 500 chars
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        
        return None
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from text"""
        text_lower = text.lower()
        found_skills = set()
        
        # Find skills from database
        for skill in self.skills_database:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill.title())
        
        return sorted(list(found_skills))
    
    def find_section(self, text: str, section_type: str) -> Optional[str]:
        """Find and extract a specific section from resume"""
        headers = self.section_headers.get(section_type, [])
        text_lower = text.lower()
        
        for header in headers:
            # Find section header
            pattern = rf'\b{re.escape(header)}\b'
            match = re.search(pattern, text_lower)
            
            if match:
                start_idx = match.end()
                
                # Find next section (any header from any category)
                all_headers = [h for headers in self.section_headers.values() for h in headers]
                next_section_idx = len(text)
                
                for next_header in all_headers:
                    if next_header == header:
                        continue
                    next_pattern = rf'\b{re.escape(next_header)}\b'
                    next_match = re.search(next_pattern, text_lower[start_idx:])
                    if next_match:
                        potential_idx = start_idx + next_match.start()
                        next_section_idx = min(next_section_idx, potential_idx)
                
                return text[start_idx:next_section_idx].strip()
        
        return None
    
    def parse_experience_section(self, experience_text: str) -> List[Dict]:
        """Parse work experience section into structured format"""
        if not experience_text:
            return []
        
        experiences = []
        doc = self.nlp(experience_text)
        
        # Split by job entries (look for date patterns as separators)
        lines = experience_text.split('\n')
        current_job = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for date patterns (likely indicates new job)
            date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
            if re.search(date_pattern, line):
                if current_job:
                    experiences.append(current_job)
                current_job = {'dates': line, 'responsibilities': []}
            elif 'responsibilities' in current_job:
                current_job['responsibilities'].append(line)
            else:
                # Likely job title or company
                if 'title' not in current_job:
                    current_job['title'] = line
                elif 'company' not in current_job:
                    current_job['company'] = line
        
        if current_job:
            experiences.append(current_job)
        
        return experiences
    
    def parse_education_section(self, education_text: str) -> List[Dict]:
        """Parse education section"""
        if not education_text:
            return []
        
        education_entries = []
        lines = education_text.split('\n')
        
        current_edu = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for degree keywords
            degree_keywords = ['bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'b.a.', 'm.a.']
            if any(keyword in line.lower() for keyword in degree_keywords):
                if current_edu:
                    education_entries.append(current_edu)
                current_edu = {'degree': line}
            elif 'degree' in current_edu and 'institution' not in current_edu:
                current_edu['institution'] = line
            elif 'institution' in current_edu and re.search(r'\d{4}', line):
                current_edu['dates'] = line
        
        if current_edu:
            education_entries.append(current_edu)
        
        return education_entries
    
    def generate_candidate_id(self, name: str = None, email: str = None) -> str:
        """Generate a unique anonymous ID for the candidate"""
        # Use name/email for consistent ID generation, or random if not available
        if name or email:
            identifier = f"{name or ''}{email or ''}"
            # Create hash for anonymity
            hash_obj = hashlib.sha256(identifier.encode())
            hash_hex = hash_obj.hexdigest()[:12]  # Use first 12 chars
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
    
    def anonymize_location(self, location: str) -> str:
        """Generalize location to city/state level only"""
        if not location:
            return None
        
        # Remove street addresses, zip codes
        # Keep only city and state
        location = re.sub(r'\d{5}(-\d{4})?', '', location)  # Remove ZIP
        location = re.sub(r'\d+\s+\w+\s+(street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)', '', location, flags=re.IGNORECASE)
        
        return location.strip()
    
    def anonymize_resume_data(self, resume: ResumeData) -> ResumeData:
        """Anonymize all personal information in resume data"""
        
        # Generate anonymous candidate ID
        resume.candidate_id = self.generate_candidate_id(resume.name, resume.email)
        
        # Remove direct identifiers
        original_name = resume.name
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
    
    def parse(self, anonymize: bool = False) -> ResumeData:
        """Main parsing function - extract all data from resume
        
        Args:
            pdf_path: Path to PDF file
            anonymize: If True, remove personal identifying information
        """
        # Extract and clean text
        raw_text = self.extract_text(self.pdf_path)
        cleaned_text = self.clean_text(raw_text)
        
        # Initialize resume data
        resume = ResumeData()
        
        # Extract basic contact info
        resume.name = self.extract_name(raw_text)
        resume.email = self.extract_email(cleaned_text)
        resume.phone = self.extract_phone(cleaned_text)
        
        # Extract location (first GPE entity)
        doc = self.nlp(raw_text[:500])
        for ent in doc.ents:
            if ent.label_ == "GPE":
                resume.location = ent.text
                break
        
        # Extract sections
        summary_text = self.find_section(raw_text, 'summary')
        if summary_text:
            resume.summary = summary_text[:500]  # Limit length
        
        # Extract skills
        resume.skills = self.extract_skills(cleaned_text)
        
        # Extract experience
        experience_text = self.find_section(raw_text, 'experience')
        resume.experience = self.parse_experience_section(experience_text)
        
        # Extract education
        education_text = self.find_section(raw_text, 'education')
        resume.education = self.parse_education_section(education_text)
        
        # Anonymize if requested
        if anonymize:
            resume = self.anonymize_resume_data(resume)
        
        return resume.to_json()