from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



resume_skills = {
    "cand_1": ["python", "data visualization", "sql", "power bi"],
    "cand_2": ["java", "machine learning", "tensorflow"],
    "cand_3": ["python", "pandas", "data analysis"]
}

job_skills = ["python", "data analysis", "sql", "machine learning"]




model = SentenceTransformer("all-MiniLM-L6-v2")

job_embeds = model.encode(job_skills)

def skill_match_score(candidate_skills, threshold=0.5):
    cand_embeds = model.encode(candidate_skills)
    
    similarity_matrix = cosine_similarity(cand_embeds, job_embeds)

    # For each candidate skill, check if it matches ANY job skill
    matched = (similarity_matrix.max(axis=1) >= threshold)
    
    return matched.sum() / len(job_skills)
scores = {}
for cand_id, skills in resume_skills.items():
    scores[cand_id] = skill_match_score(skills)

for cand_id, score in scores.items():
    print(f"{cand_id}: Fair score rating {score * 10:.1f}/10")
