from sentence_transformers import SentenceTransformer, CrossEncoder, util
import torch
import spacy
import numpy as np

class SemanticMatcher:
    def __init__(self, bi_encoder_name: str = 'all-MiniLM-L6-v2', cross_encoder_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2', spacy_model: str = "en_core_web_sm"):
        """
        Initializes the models.
        - Bi-Encoder: For fast information retrieval and generating embeddings.
        - Cross-Encoder: For accurate scoring of sentence pairs (Job Description <-> Resume).
        - Spacy: For Entity Extraction (Skills, Experience).
        """
        self.bi_encoder = SentenceTransformer(bi_encoder_name)
        self.cross_encoder = CrossEncoder(cross_encoder_name)
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Spacy model '{spacy_model}' not found. Loading blank 'en' model.")
            self.nlp = spacy.blank("en")

    def _extract_entities(self, text: str) -> dict:
        """
        Extracts named entities to simulate 'Hard Skills', 'Experience', and 'Education'.
        Since standard models don't have specific tags, we use proxies:
        - Skills: ORG, PRODUCT, GPE, LANGUAGE (excluding education keywords)
        - Experience: DATE
        - Education: ORG entities containing education-related keywords
        """
        doc = self.nlp(text)
        entities = {
            "skills": [],
            "experience": [],
            "education": []
        }
        
        education_keywords = {"university", "college", "school", "institute", "academy", "bachelor", "master", "phd", "degree"}
        
        for ent in doc.ents:
            text_lower = ent.text.lower()
            if ent.label_ == "DATE":
                entities["experience"].append(ent.text)
            elif ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "GPE", "LANGUAGE"]:
                # Simple heuristic to separate Education from generic ORG/Skills
                if any(keyword in text_lower for keyword in education_keywords):
                    entities["education"].append(ent.text)
                else:
                    entities["skills"].append(ent.text)
        
        return entities

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Computes the cosine similarity between two texts using the Bi-Encoder.
        Good for fast filtering.
        """
        embeddings = self.bi_encoder.encode([text1, text2], convert_to_tensor=True)
        cosine_scores = util.cos_sim(embeddings[0], embeddings[1])
        return float(cosine_scores[0][0])

    def evaluate_match(self, job_description: str, resume_text: str) -> float:
        """
        Evaluates the relevance using the Cross-Encoder.
        Returns a normalized score (0 to 1) using sigmoid.
        """
        logits = self.cross_encoder.predict([(job_description, resume_text)])
        # Apply sigmoid to convert logits to probability/score 0-1
        score = 1 / (1 + np.exp(-logits[0]))
        return float(score)

    def compute_entity_weighted_score(self, job_description: str, resume_text: str) -> float:
        """
        Calculates a semantic similarity score focused on extracted entities.
        Weights: Skills (0.4), Experience (0.5), Education (0.1).
        """
        jd_ents = self._extract_entities(job_description)
        res_ents = self._extract_entities(resume_text)

        # Convert entity lists back to specific strings for embedding comparison
        jd_skills_text = " ".join(jd_ents["skills"])
        res_skills_text = " ".join(res_ents["skills"])
        
        jd_exp_text = " ".join(jd_ents["experience"])
        res_exp_text = " ".join(res_ents["experience"])
        
        jd_edu_text = " ".join(jd_ents["education"])
        res_edu_text = " ".join(res_ents["education"])

        # Calculate Similarity for Skills (Weight: 0.4)
        if jd_skills_text and res_skills_text:
            skills_sim = self.compute_similarity(jd_skills_text, res_skills_text)
        else:
            skills_sim = 0.0

        # Calculate Similarity for Experience (Weight: 0.5)
        if jd_exp_text and res_exp_text:
            exp_sim = self.compute_similarity(jd_exp_text, res_exp_text)
        else:
            exp_sim = 0.0

        # Calculate Similarity for Education (Weight: 0.1)
        if jd_edu_text and res_edu_text:
            edu_sim = self.compute_similarity(jd_edu_text, res_edu_text)
        else:
            edu_sim = 0.0

        return (0.4 * skills_sim) + (0.5 * exp_sim) + (0.1 * edu_sim)

    def get_combined_score(self, job_description: str, resume_text: str) -> dict:
        """
        Combines Cross-Encoder Score and Entity-Weighted Score for a final robust metric.
        """
        # 1. Nuanced semantic match (Cross-Encoder)
        ce_score = self.evaluate_match(job_description, resume_text)
        
        # 2. Entity-focused match (Hard Skills & Experience)
        entity_score = self.compute_entity_weighted_score(job_description, resume_text)
        
        # Final Weighted Score (Adjust weights as needed)
        # We give slight preference to the deep semantic textual match of the Cross-Encoder
        final_score = (0.6 * ce_score) + (0.4 * entity_score)
        
        return {
            "final_score": round(final_score, 4),
            "cross_encoder_score": round(ce_score, 4),
            "entity_score": round(entity_score, 4)
        }

    def rank_candidates(self, job_description: str, resumes: list[str]) -> list[tuple[int, float, dict]]:
        """
        Two-stage ranking:
        1. Bi-Encoder: Fast retrieval of top candidates (e.g., Top 10 or Top 20%).
        2. Cross-Encoder + Entity Weighted: Detailed re-ranking of top candidates.
        
        Returns: List of (index, final_score, details_dict) sorted by score.
        """
        if not resumes:
            return []

        # -- Stage 1: Fast Filter (Bi-Encoder) --
        
        # Encode all resumes and JD
        job_embedding = self.bi_encoder.encode(job_description, convert_to_tensor=True)
        resume_embeddings = self.bi_encoder.encode(resumes, convert_to_tensor=True)
        
        # Compute Cosine Similarity
        cosine_scores = util.cos_sim(job_embedding, resume_embeddings)[0]
        
        # Create initial ranked list (index, score)
        initial_ranking = []
        for i, score in enumerate(cosine_scores):
            initial_ranking.append((i, float(score)))
        
        # Sort by cosine similarity descending
        initial_ranking.sort(key=lambda x: x[1], reverse=True)
        
        # Keep top 10 (or all if less than 10) for expensive re-ranking
        top_k = min(10, len(initial_ranking))
        candidates_to_rerank = initial_ranking[:top_k]
        
        # -- Stage 2: Detailed Re-ranking --
        final_results = []
        
        for idx, base_score in candidates_to_rerank:
            resume_text = resumes[idx]
            scores = self.get_combined_score(job_description, resume_text)
            final_results.append((idx, scores["final_score"], scores))
            
        # Sort final results by the computed final score
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return final_results

# Singleton instance
matcher_instance = SemanticMatcher()
