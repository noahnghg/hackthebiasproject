import pdfplumber
import spacy
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json


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
    anonymized: bool = False
    candidate_id: Optional[str] = None
    
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
    
    def to_sentence_transformer_format(self) -> Dict[str, str]:
        """Convert resume to format optimized for sentence transformers
        
        Returns a dictionary with structured text segments ready for embedding
        """
        segments = {}
        
        # 1. Profile segment - high-level overview
        profile_parts = []
        if self.location:
            profile_parts.append(f"Location: {self.location}")
        if self.summary:
            profile_parts.append(self.summary)
        if self.skills:
            profile_parts.append(f"Technical Skills: {', '.join(self.skills)}")
        
        segments['profile'] = ' '.join(profile_parts)
        
        # 2. Skills segment - just the skills list for easy matching
        segments['skills'] = ', '.join(self.skills) if self.skills else ''
        
        # 3. Experience segments - one text block per job
        experience_texts = []
        for i, exp in enumerate(self.experience):
            exp_parts = []
            if exp.get('title'):
                exp_parts.append(f"Position: {exp['title']}")
            if exp.get('company'):
                exp_parts.append(f"Company: {exp['company']}")
            if exp.get('dates'):
                exp_parts.append(f"Duration: {exp['dates']}")
            if exp.get('responsibilities'):
                exp_parts.append("Responsibilities: " + ' '.join(exp['responsibilities']))
            
            experience_texts.append(' '.join(exp_parts))
        
        segments['experience'] = ' | '.join(experience_texts)
        
        # 4. Education segment
        education_texts = []
        for edu in self.education:
            edu_parts = []
            if edu.get('degree'):
                edu_parts.append(edu['degree'])
            if edu.get('institution'):
                edu_parts.append(edu['institution'])
            if edu.get('dates'):
                edu_parts.append(edu['dates'])
            education_texts.append(' '.join(edu_parts))
        
        segments['education'] = ' | '.join(education_texts)
        
        # 5. Full text - everything combined for general semantic search
        full_text_parts = [
            segments['profile'],
            segments['experience'],
            segments['education']
        ]
        segments['full_text'] = ' '.join(filter(None, full_text_parts))
        
        # Add metadata
        segments['candidate_id'] = self.candidate_id or 'UNKNOWN'
        segments['is_anonymized'] = str(self.anonymized)
        
        return segments
    
    def to_sentence_list(self) -> List[str]:
        """Convert resume to a list of sentences for batch embedding
        
        Useful for creating embeddings of each sentence separately
        """
        sentences = []
        
        # Add summary sentences
        if self.summary:
            # Split by periods, clean up
            summary_sentences = [s.strip() + '.' for s in self.summary.split('.') if s.strip()]
            sentences.extend(summary_sentences)
        
        # Add experience bullets
        for exp in self.experience:
            if exp.get('responsibilities'):
                sentences.extend(exp['responsibilities'])
        
        return sentences


class ResumeParser:
    """Parse resume PDFs and extract structured data"""
    
    def __init__(self, pdf_path: str, spacy_model="en_core_web_sm"):
        """Initialize parser with spaCy model and PDF path"""
        if not pdf_path:
            raise ValueError("pdf_path must be provided")

        self.pdf_path = pdf_path
        
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Model '{spacy_model}' not found. Run: python -m spacy download {spacy_model}")
            raise
        
        # Common technical skills database
        self.skills_database = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'node.js', 'express',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'terraform',
            'postgresql', 'mysql', 'mongodb', 'redis', 'cassandra', 'elasticsearch',
            'git', 'github', 'gitlab', 'jira', 'agile', 'scrum',
            'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'spacy', 'spark', 'hadoop', 'kafka'
        }
        
        # Section headers to look for
        self.section_headers = {
            'experience': ['experience', 'work experience', 'employment', 'professional experience'],
            'education': ['education', 'academic background', 'qualification'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
            'summary': ['summary', 'profile', 'professional summary', 'about']
        }
    
    def extract_text(self) -> str:
        """Extract text from PDF"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text - remove bullets and special characters"""
        # Remove common bullet points and special characters
        text = re.sub(r'[●•◆▪▸➤⦿✓✔]', '', text)
        
        # Remove Unicode bullet characters like \u25cf
        text = re.sub(r'[\u25cf\u25cb\u25aa\u25ab\u2022\u2023\u2043\u204c\u204d\u2219\u25e6]', '', text)
        
        # Remove other common special characters but keep useful punctuation
        text = re.sub(r'[^\w\s.,;:!?()\-@/#$%&+="\'<>\n]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Clean up multiple newlines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address using regex"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
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
        doc = self.nlp(text[:500])
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
    
    def parse(self) -> ResumeData:
        """Main parsing function - extract all data from resume"""
        # Extract and clean text
        raw_text = self.extract_text()
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
            resume.summary = summary_text[:500]
        
        # Extract skills
        resume.skills = self.extract_skills(cleaned_text)
        
        # Extract experience
        experience_text = self.find_section(raw_text, 'experience')
        resume.experience = self.parse_experience_section(experience_text)
        
        # Extract education
        education_text = self.find_section(raw_text, 'education')
        resume.education = self.parse_education_section(education_text)
        
        return resume