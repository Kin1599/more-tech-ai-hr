"""
ML модуль для определения схожести резюме на основе эмбеддингов и косинусной близости.
Использует sentence-transformers для генерации эмбеддингов и numpy для вычислений.
"""

import os
import re
import hashlib
import pickle
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
from sqlalchemy.orm import Session

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")

from ..models.models import JobApplication, ApplicantResumeVersion, ApplicantProfile


class ResumeEmbeddingModel:
    """Класс для работы с эмбеддингами резюме."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Инициализация модели эмбеддингов.
        
        Args:
            model_name: Название модели sentence-transformers
        """
        self.model_name = model_name
        self.model = None
        self.cache_dir = "/tmp/resume_embeddings_cache"
        
        # Создаем директорию для кеша, если она не существует
        os.makedirs(self.cache_dir, exist_ok=True)
        
 
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                print(f"Loaded sentence-transformers model: {model_name}")
            except Exception as e:
                print(f"Error loading sentence-transformers model: {e}")
                self.model = None
        print(f"SentenceTransformer model loading disabled for faster startup")
        
    def _clean_text(self, text: str) -> str:
        """Очистка и нормализация текста."""
        if not text:
            return ""
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Удаляем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text)
        
        # Удаляем специальные символы, оставляем буквы, цифры, пробелы и базовую пунктуацию
        text = re.sub(r'[^\w\s.,!?;:()\-]', ' ', text)
        
        # Удаляем повторяющиеся пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _get_cache_key(self, text: str) -> str:
        """Генерация ключа кеша для текста."""
        cleaned_text = self._clean_text(text)
        return hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """Загрузка эмбеддинга из кеша."""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading from cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: np.ndarray) -> None:
        """Сохранение эмбеддинга в кеш."""
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Получение эмбеддинга для текста с кешированием.
        
        Args:
            text: Текст для преобразования в эмбеддинг
            
        Returns:
            Эмбеддинг как numpy array или None в случае ошибки
        """
        if not text or not text.strip():
            return None
        
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return None
        
        # Проверяем кеш
        cache_key = self._get_cache_key(text)
        cached_embedding = self._load_from_cache(cache_key)
        if cached_embedding is not None:
            return cached_embedding
        
        # Если модель недоступна, используем простой fallback
        if not self.model:
            return self._simple_text_embedding(cleaned_text)
        
        try:
            # Генерируем эмбеддинг
            embedding = self.model.encode(cleaned_text, convert_to_numpy=True)
            
            # Сохраняем в кеш
            self._save_to_cache(cache_key, embedding)
            
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return self._simple_text_embedding(cleaned_text)
    
    def _simple_text_embedding(self, text: str) -> np.ndarray:
        """
        Простой fallback для создания эмбеддинга без sentence-transformers.
        Создает векторное представление на основе частотности слов.
        """
        words = text.split()
        if not words:
            return np.zeros(384)  # Размер совместимый с all-MiniLM-L6-v2
        
        # Создаем простой TF-IDF подобный вектор
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Берем топ-384 самых частых слов и создаем вектор
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:384]
        
        embedding = np.zeros(384)
        for i, (word, count) in enumerate(sorted_words):
            if i < 384:
                # Простая нормализация на основе частотности и позиции
                embedding[i] = count / len(words) * (1.0 - i / 384)
        
        # Нормализуем вектор
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding


def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Вычисление косинусной близости между двумя эмбеддингами.
    
    Args:
        embedding1: Первый эмбеддинг
        embedding2: Второй эмбеддинг
        
    Returns:
        Косинусная близость (от 0 до 1)
    """
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    try:
        # Вычисляем косинусную близость
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Приводим к диапазону [0, 1]
        similarity = (similarity + 1) / 2
        
        return float(similarity)
    except Exception as e:
        print(f"Error calculating cosine similarity: {e}")
        return 0.0


def extract_resume_features(text: str) -> Dict[str, Any]:
    """
    Извлечение ключевых особенностей резюме для дополнительного анализа.
    
    Args:
        text: Текст резюме
        
    Returns:
        Словарь с извлеченными особенностями
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    
    # Поиск ключевых разделов и навыков
    features = {
        'skills': [],
        'experience_years': 0,
        'education_level': '',
        'technologies': [],
        'languages': [],
        'sections': []
    }
    
    # Технологии и навыки (расширенный список)
    tech_keywords = [
        'python', 'java', 'javascript', 'react', 'vue', 'angular', 'node.js',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp', 'git', 'linux', 'windows', 'macos',
        'html', 'css', 'typescript', 'php', 'ruby', 'go', 'rust',
        'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch'
    ]
    
    for tech in tech_keywords:
        if tech in text_lower:
            features['technologies'].append(tech)
    
    # Языки программирования и человеческие языки
    languages = ['english', 'русский', 'german', 'french', 'spanish', 'chinese']
    for lang in languages:
        if lang in text_lower:
            features['languages'].append(lang)
    
    # Поиск опыта работы (в годах)
    experience_patterns = [
        r'(\d+)\s*(?:лет|год|года)',
        r'(\d+)\s*years?',
        r'опыт\s*(\d+)',
        r'experience\s*(\d+)'
    ]
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                years = max([int(match) for match in matches])
                features['experience_years'] = years
                break
            except ValueError:
                continue
    
    # Определение уровня образования
    education_keywords = {
        'phd': ['phd', 'кандидат наук', 'доктор'],
        'master': ['master', 'магистр', 'mba'],
        'bachelor': ['bachelor', 'бакалавр', 'специалист'],
        'college': ['колледж', 'техникум', 'college']
    }
    
    for level, keywords in education_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            features['education_level'] = level
            break
    
    # Поиск разделов резюме
    section_keywords = [
        'опыт работы', 'образование', 'навыки', 'достижения',
        'experience', 'education', 'skills', 'achievements'
    ]
    
    for section in section_keywords:
        if section in text_lower:
            features['sections'].append(section)
    
    return features


def calculate_feature_similarity(features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
    """
    Вычисление схожести на основе извлеченных особенностей.
    
    Args:
        features1: Особенности первого резюме
        features2: Особенности второго резюме
        
    Returns:
        Коэффициент схожести (от 0 до 1)
    """
    if not features1 or not features2:
        return 0.0
    
    similarity_scores = []
    
    # Схожесть технологий
    tech1 = set(features1.get('technologies', []))
    tech2 = set(features2.get('technologies', []))
    if tech1 or tech2:
        tech_similarity = len(tech1.intersection(tech2)) / len(tech1.union(tech2)) if tech1.union(tech2) else 0
        similarity_scores.append(tech_similarity * 0.4)  # 40% веса
    
    # Схожесть языков
    lang1 = set(features1.get('languages', []))
    lang2 = set(features2.get('languages', []))
    if lang1 or lang2:
        lang_similarity = len(lang1.intersection(lang2)) / len(lang1.union(lang2)) if lang1.union(lang2) else 0
        similarity_scores.append(lang_similarity * 0.2)  # 20% веса
    
    # Схожесть разделов
    sect1 = set(features1.get('sections', []))
    sect2 = set(features2.get('sections', []))
    if sect1 or sect2:
        sect_similarity = len(sect1.intersection(sect2)) / len(sect1.union(sect2)) if sect1.union(sect2) else 0
        similarity_scores.append(sect_similarity * 0.2)  # 20% веса
    
    # Схожесть опыта работы
    exp1 = features1.get('experience_years', 0)
    exp2 = features2.get('experience_years', 0)
    if exp1 > 0 and exp2 > 0:
        exp_similarity = 1 - abs(exp1 - exp2) / max(exp1, exp2, 10)  # Нормализуем относительно максимума
        similarity_scores.append(max(0, exp_similarity) * 0.1)  # 10% веса
    
    # Схожесть образования
    edu1 = features1.get('education_level', '')
    edu2 = features2.get('education_level', '')
    if edu1 and edu2:
        edu_similarity = 1.0 if edu1 == edu2 else 0.0
        similarity_scores.append(edu_similarity * 0.1)  # 10% веса
    
    return sum(similarity_scores) if similarity_scores else 0.0


# Глобальный экземпляр модели (ленивая инициализация)
_embedding_model = None

def get_embedding_model() -> ResumeEmbeddingModel:
    """Получение глобального экземпляра модели эмбеддингов."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = ResumeEmbeddingModel()
    return _embedding_model


def find_similar_resumes(
    db: Session,
    current_application_id: int,
    vacancy_id: int,
    similarity_threshold: float = 0.75
) -> Optional[int]:
    """
    Находит похожие резюме среди кандидатов на ту же вакансию с использованием ML.
    
    Args:
        db: Сессия базы данных
        current_application_id: ID текущей заявки
        vacancy_id: ID вакансии
        similarity_threshold: Порог схожести (по умолчанию 0.75)
        
    Returns:
        ID кандидата с наиболее похожим резюме или None
    """
    # Получаем текущую заявку
    current_application = db.query(JobApplication).filter_by(id=current_application_id).first()
    if not current_application:
        return None
    
    # Получаем профиль текущего кандидата и его резюме
    current_applicant = (
        db.query(ApplicantProfile)
        .filter_by(id=current_application.applicant_id)
        .first()
    )
    
    if not current_applicant or not current_applicant.cv:
        return None
    
    # Получаем все другие заявки на ту же вакансию (поданные раньше)
    other_applications = (
        db.query(JobApplication)
        .filter(
            JobApplication.vacancy_id == vacancy_id,
            JobApplication.id != current_application_id,
            JobApplication.created_at < current_application.created_at
        )
        .all()
    )
    
    if not other_applications:
        return None
    
    # Инициализируем модель
    model = get_embedding_model()
    
    # Получаем эмбеддинг и особенности текущего резюме
    current_text = current_applicant.cv
    current_embedding = model.get_embedding(current_text)
    current_features = extract_resume_features(current_text)
    
    if current_embedding is None:
        return None
    
    max_similarity = 0.0
    most_similar_applicant_id = None
    
    for other_app in other_applications:
        # Получаем профиль другого кандидата
        other_applicant = (
            db.query(ApplicantProfile)
            .filter_by(id=other_app.applicant_id)
            .first()
        )
        
        if not other_applicant or not other_applicant.cv:
            continue
        
        other_text = other_applicant.cv
        other_embedding = model.get_embedding(other_text)
        other_features = extract_resume_features(other_text)
        
        if other_embedding is None:
            continue
        
        # Вычисляем косинусную близость эмбеддингов
        embedding_similarity = cosine_similarity(current_embedding, other_embedding)
        
        # Вычисляем схожесть особенностей
        feature_similarity = calculate_feature_similarity(current_features, other_features)
        
        # Комбинированная оценка схожести
        # 70% веса на эмбеддинги, 30% на особенности
        combined_similarity = (embedding_similarity * 0.7) + (feature_similarity * 0.3)
        
        if combined_similarity > max_similarity:
            max_similarity = combined_similarity
            most_similar_applicant_id = other_app.applicant_id
    
    # Возвращаем ID наиболее похожего кандидата, если схожесть превышает порог
    if max_similarity >= similarity_threshold:
        return most_similar_applicant_id
    
    return None


def check_all_applications_similarity(db: Session, vacancy_id: int) -> Dict[int, Optional[int]]:
    """
    Проверяет схожесть резюме для всех заявок на вакансию с использованием ML.
    Оптимизированная версия с предварительной загрузкой данных.
    
    Args:
        db: Сессия базы данных
        vacancy_id: ID вакансии
        
    Returns:
        Словарь {application_id: similar_applicant_id}
    """
    from sqlalchemy.orm import joinedload
    
    # Получаем все заявки с профилями кандидатов за один запрос
    applications = (
        db.query(JobApplication)
        .options(joinedload(JobApplication.applicant_profile))
        .filter_by(vacancy_id=vacancy_id)
        .order_by(JobApplication.created_at)
        .all()
    )
    
    if not applications:
        return {}
    
    # Инициализируем модель один раз
    model = get_embedding_model()
    
    # Предварительно вычисляем эмбеддинги для всех резюме
    app_embeddings = {}
    app_features = {}
    
    for app in applications:
        if app.applicant_profile and app.applicant_profile.cv:
            text = app.applicant_profile.cv
            embedding = model.get_embedding(text)
            features = extract_resume_features(text)
            
            if embedding is not None:
                app_embeddings[app.id] = embedding
                app_features[app.id] = features
    
    # Вычисляем схожесть между всеми парами
    similarity_results = {}
    
    for i, current_app in enumerate(applications):
        if current_app.id not in app_embeddings:
            similarity_results[current_app.id] = None
            continue
            
        current_embedding = app_embeddings[current_app.id]
        current_features = app_features[current_app.id]
        
        max_similarity = 0.0
        most_similar_applicant_id = None
        
        # Сравниваем только с более ранними заявками
        for earlier_app in applications[:i]:
            if earlier_app.id not in app_embeddings:
                continue
                
            other_embedding = app_embeddings[earlier_app.id]
            other_features = app_features[earlier_app.id]
            
            # Вычисляем косинусную близость эмбеддингов
            embedding_similarity = cosine_similarity(current_embedding, other_embedding)
            
            # Вычисляем схожесть особенностей
            feature_similarity = calculate_feature_similarity(current_features, other_features)
            
            # Комбинированная оценка схожести (70% эмбеддинги, 30% особенности)
            combined_similarity = (embedding_similarity * 0.7) + (feature_similarity * 0.3)
            
            if combined_similarity > max_similarity:
                max_similarity = combined_similarity
                most_similar_applicant_id = earlier_app.applicant_id
        
        # Сохраняем результат, если схожесть превышает порог
        if max_similarity >= 0.75:  # порог схожести
            similarity_results[current_app.id] = most_similar_applicant_id
        else:
            similarity_results[current_app.id] = None
    
    return similarity_results
