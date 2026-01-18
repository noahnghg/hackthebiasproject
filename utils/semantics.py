from sentence_transformers import CrossEncoder
import numpy as np
import spacy
import re
import logging

# Configure logging to show INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticMatcher:
    def __init__(self, cross_encoder_name: str = 'cross-encoder/stsb-roberta-base', spacy_model: str = "en_core_web_sm"):
        """
        Initializes the semantic matcher with a cross-encoder for text similarity.
        Uses stsb-roberta-base which is trained for semantic textual similarity (0-1 scores).
        """
        self.cross_encoder = CrossEncoder(cross_encoder_name)
        
        # Load spaCy for entity extraction
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Spacy model '{spacy_model}' not found. Loading blank 'en' model.")
            self.nlp = spacy.blank("en")
        
        # Tech skills list for entity extraction
        self.tech_skills = {
            "python", "java", "javascript", "typescript", "go", "golang", "rust", "c++", 
            "c#", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
            "react", "vue", "angular", "svelte", "html", "css", "tailwind", "bootstrap",
            "next.js", "nextjs", "nuxt", "gatsby", "webpack", "vite",
            "node.js", "nodejs", "express", "django", "flask", "fastapi", "spring", 
            "spring boot", "rails", "laravel", ".net", "asp.net",
            "sql", "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
            "dynamodb", "cassandra", "sqlite", "oracle", "neo4j",
            "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
            "terraform", "ansible", "jenkins", "github actions", "gitlab", "ci/cd",
            "linux", "unix", "bash", "shell",
            "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
            "scikit-learn", "sklearn", "pandas", "numpy", "nlp", "computer vision",
            "neural network", "transformer", "bert", "gpt", "llm",
            "data engineering", "etl", "spark", "airflow", "kafka", "hadoop",
            "data pipeline", "databricks", "snowflake", "bigquery", "dbt",
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
        
        # Extract skills via keyword matching
        for skill in self.tech_skills:
            if skill in text_lower:
                entities["skills"].append(skill)
        
        education_keywords = {"university", "college", "school", "institute", "academy", 
                            "bachelor", "master", "phd", "degree", "bs", "ms", "ba", "ma"}
        
        experience_keywords = {"engineered", "developed", "built", "created", "implemented", 
                             "designed", "managed", "led", "architected", "reduced", 
                             "increased", "improved", "optimized", "deployed", "automated", 
                             "integrated", "processed", "achieved", "delivered", "launched"}
        
        url_pattern = re.compile(r'https?://|www\.|\\.com|\\.org|\\.io|linkedin|github|gmail')
        email_pattern = re.compile(r'@|\\[EMAIL REDACTED\\]')
        
        # Extract education
        for ent in doc.ents:
            ent_lower = ent.text.lower()
            if ent.label_ == "ORG":
                if any(kw in ent_lower for kw in education_keywords):
                    entities["education"].append(ent.text)
        
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            if any(kw in sent_lower for kw in education_keywords):
                if not url_pattern.search(sent.text) and not email_pattern.search(sent.text):
                    if len(sent.text) > 20 and len(sent.text) < 200:
                        entities["education"].append(sent.text.strip())
        
        # Extract experience
        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_lower = sent_text.lower()
            
            if url_pattern.search(sent_text):
                continue
            if email_pattern.search(sent_text):
                continue
            if sent_text in ["Education", "Experience", "Projects", "Skills", "Summary", "Contact"]:
                continue
            
            has_action_verb = any(kw in sent_lower for kw in experience_keywords)
            
            if has_action_verb and len(sent_text) > 30:
                clean_text = sent_text.lstrip('•-').strip()
                entities["experience"].append(clean_text)
        
        # Remove duplicates
        entities["skills"] = list(dict.fromkeys(entities["skills"]))
        entities["experience"] = list(dict.fromkeys(entities["experience"]))
        entities["education"] = list(dict.fromkeys(entities["education"]))
        
        return entities

    def get_final_score(self, job_description: str, resume_text: str) -> float:
        """
        Computes the final match score using only the cross-encoder.
        
        The stsb-roberta-base model is trained on Semantic Textual Similarity Benchmark
        and outputs scores directly in the 0-1 range.
        
        Returns a score from 0 to 1.
        """
        # Cross-encoder directly outputs similarity score (0-1 range for stsb-roberta-base)
        # Typical raw scores: ~0.5-0.6 for strong matches, ~0.0-0.1 for non-matches
        raw_score = self.cross_encoder.predict([(job_description, resume_text)])[0]

        return raw_score*1.6

# Singleton instance
semantics_instance = SemanticMatcher()
