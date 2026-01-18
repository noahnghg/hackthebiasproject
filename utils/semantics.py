from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
import spacy
import re

class SemanticMatcher:
    def __init__(self, bi_encoder_name: str = 'all-MiniLM-L6-v2', spacy_model: str = "en_core_web_sm"):
        """
        Initializes the semantic matcher with a bi-encoder for text similarity.
        """
        self.bi_encoder = SentenceTransformer(bi_encoder_name)
        
        # Load spaCy for entity extraction
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Spacy model '{spacy_model}' not found. Loading blank 'en' model.")
            self.nlp = spacy.blank("en")
        
        # Comprehensive tech skills list for keyword matching
        self.tech_skills = {
            # Languages
            "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++", 
            "c#", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
            # Frontend
            "react", "vue", "angular", "svelte", "html", "css", "tailwind", "bootstrap",
            "next.js", "nextjs", "nuxt", "gatsby", "webpack", "vite",
            # Backend
            "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring", 
            "spring boot", "rails", "laravel", ".net", "asp.net",
            # Databases
            "sql", "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
            "dynamodb", "cassandra", "sqlite", "oracle", "neo4j",
            # Cloud & DevOps
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
            "terraform", "ansible", "jenkins", "github actions", "gitlab", "ci/cd",
            "linux", "unix", "bash", "shell",
            # ML/AI
            "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
            "scikit-learn", "sklearn", "pandas", "numpy", "nlp", "computer vision",
            "neural network", "transformer", "bert", "gpt", "llm",
            # Data
            "data engineering", "etl", "spark", "airflow", "kafka", "hadoop",
            "data pipeline", "databricks", "snowflake", "bigquery", "dbt",
            # Other
            "git", "agile", "scrum", "microservices", "rest", "api", "graphql",
            "grpc", "rabbitmq", "celery", "nginx", "apache"
        }

    def _extract_entities(self, text: str) -> dict:
        """
        Extracts structured entities from text:
        - Skills: Technical skills found via keyword matching
        - Experience: Bullet points with action verbs describing work
        - Education: Educational institutions and degrees
        """
        doc = self.nlp(text)
        entities = {
            "skills": [],
            "experience": [],
            "education": []
        }
        
        text_lower = text.lower()
        
        # Extract skills via keyword matching (more reliable than NER for tech terms)
        for skill in self.tech_skills:
            if skill in text_lower:
                entities["skills"].append(skill)
        
        # Education keywords for filtering
        education_keywords = {"university", "college", "school", "institute", "academy", 
                            "bachelor", "master", "phd", "degree", "bs", "ms", "ba", "ma"}
        
        # Experience action verbs
        experience_keywords = {"engineered", "developed", "built", "created", "implemented", 
                             "designed", "managed", "led", "architected", "reduced", 
                             "increased", "improved", "optimized", "deployed", "automated", 
                             "integrated", "processed", "achieved", "delivered", "launched"}
        
        # Patterns to filter out
        url_pattern = re.compile(r'https?://|www\.|\\.com|\\.org|\\.io|linkedin|github|gmail')
        email_pattern = re.compile(r'@|\\[EMAIL REDACTED\\]')
        
        # Extract education from NER (ORG entities with education keywords)
        for ent in doc.ents:
            ent_lower = ent.text.lower()
            if ent.label_ == "ORG":
                if any(kw in ent_lower for kw in education_keywords):
                    entities["education"].append(ent.text)
        
        # Also check sentences for education-related content
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            if any(kw in sent_lower for kw in education_keywords):
                if not url_pattern.search(sent.text) and not email_pattern.search(sent.text):
                    # Check if it's a meaningful education sentence
                    if len(sent.text) > 20 and len(sent.text) < 200:
                        entities["education"].append(sent.text.strip())
        
        # Extract experience bullet points
        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_lower = sent_text.lower()
            
            # Skip URLs, emails, headers
            if url_pattern.search(sent_text):
                continue
            if email_pattern.search(sent_text):
                continue
            if sent_text in ["Education", "Experience", "Projects", "Skills", "Summary", "Contact"]:
                continue
            
            # Include sentences with action verbs that describe accomplishments
            has_action_verb = any(kw in sent_lower for kw in experience_keywords)
            
            if has_action_verb and len(sent_text) > 30:
                clean_text = sent_text.lstrip('•-').strip()
                entities["experience"].append(clean_text)
        
        # Remove duplicates while preserving order
        entities["skills"] = list(dict.fromkeys(entities["skills"]))
        entities["experience"] = list(dict.fromkeys(entities["experience"]))
        entities["education"] = list(dict.fromkeys(entities["education"]))
        
        return entities


    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Computes cosine similarity between two texts using sentence embeddings.
        """
        if not text1.strip() or not text2.strip():
            return 0.0
        embeddings = self.bi_encoder.encode([text1, text2], convert_to_tensor=True)
        cosine_score = util.cos_sim(embeddings[0], embeddings[1])
        return float(cosine_score[0][0])

    def extract_skills(self, text: str) -> set:
        """
        Extracts tech skills from text using keyword matching.
        More reliable than NER for technical terms.
        """
        text_lower = text.lower()
        found_skills = set()
        for skill in self.tech_skills:
            if skill in text_lower:
                found_skills.add(skill)
        return found_skills

    def compute_skill_match(self, job_text: str, resume_text: str) -> float:
        """
        Computes skill overlap ratio between job requirements and resume.
        Returns percentage of required skills that the candidate has.
        """
        job_skills = self.extract_skills(job_text)
        resume_skills = self.extract_skills(resume_text)
        
        if not job_skills:
            return 0.5  # Neutral if no skills detected in job
        
        matching_skills = job_skills.intersection(resume_skills)
        match_ratio = len(matching_skills) / len(job_skills)
        
        return match_ratio

    def get_final_score(self, job_description: str, resume_text: str) -> float:
        """
        Computes the final match score between a job and resume.
        
        Uses three signals:
        1. Semantic similarity (30%) - Overall text meaning match
        2. Skill match (50%) - Explicit skill keyword overlap
        3. Context boost (20%) - Bonus for semantic similarity of skill contexts
        
        Returns a score from 0 to 1, scaled for intuitive interpretation.
        """
        # 1. Direct semantic similarity
        semantic_sim = self.compute_similarity(job_description, resume_text)
        
        # 2. Skill keyword match (most important for job matching)
        skill_match = self.compute_skill_match(job_description, resume_text)
        
        # 3. Context matching - compare the semantic meaning around skills
        job_skills = self.extract_skills(job_description)
        resume_skills = self.extract_skills(resume_text)
        
        if job_skills and resume_skills:
            # Create skill-focused text snippets
            job_skill_text = " ".join(job_skills)
            resume_skill_text = " ".join(resume_skills)
            context_sim = self.compute_similarity(job_skill_text, resume_skill_text)
        else:
            context_sim = semantic_sim  # Fallback to overall similarity
        
        # Raw weighted score
        # Skill match is weighted heavily as it's the most reliable signal
        raw_score = (0.30 * semantic_sim) + (0.50 * skill_match) + (0.20 * context_sim)
        
        # Scale the score to an intuitive range
        # Cosine similarity for related texts is typically 0.3-0.6
        # We want a "good match" (60%+ skill overlap) to show as 70%+
        # 
        # Apply a scaling transformation:
        # - Minimum realistic score: ~0.15 (unrelated)
        # - Maximum realistic score: ~0.85 (perfect match)
        # - We scale this to 0.20-0.95 range for better UX
        
        # If skill match is high, boost the score
        if skill_match >= 0.7:
            # Strong skill match - candidate has most required skills
            scaled_score = 0.70 + (raw_score * 0.30)
        elif skill_match >= 0.5:
            # Moderate skill match
            scaled_score = 0.50 + (raw_score * 0.40)
        elif skill_match >= 0.3:
            # Some skill overlap
            scaled_score = 0.35 + (raw_score * 0.45)
        else:
            # Limited skill overlap - rely more on semantic similarity
            scaled_score = raw_score * 1.2  # Slight boost for semantic component
        
        # Ensure score is in valid range
        final_score = max(0.15, min(0.95, scaled_score))
        
        return round(final_score, 3)


# Singleton instance
semantics_instance = SemanticMatcher()
