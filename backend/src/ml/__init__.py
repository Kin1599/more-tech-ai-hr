"""
ML модули для HR системы.
Включает в себя алгоритмы для анализа резюме, определения схожести и других ML задач.
"""

from .resume_similarity import (
    find_similar_resumes,
    check_all_applications_similarity,
    get_embedding_model,
    cosine_similarity,
    extract_resume_features,
    calculate_feature_similarity,
    ResumeEmbeddingModel
)

__all__ = [
    'find_similar_resumes',
    'check_all_applications_similarity',
    'get_embedding_model',
    'cosine_similarity',
    'extract_resume_features',
    'calculate_feature_similarity',
    'ResumeEmbeddingModel'
]
