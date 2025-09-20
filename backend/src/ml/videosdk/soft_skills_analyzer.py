"""
Soft Skills Analyzer - Анализ поведенческих паттернов и соответствия вакансии.

Модуль для анализа soft skills, фиксации пауз, эмоциональной окраски,
логической структуры ответов и NLP сопоставления с требованиями вакансии.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ResponseMetrics:
    """Метрики ответа кандидата."""
    timestamp: float
    question_id: str
    response_text: str
    response_duration: float  # длительность ответа в секундах
    pause_count: int  # количество пауз >3 сек
    total_pause_duration: float  # общая длительность пауз
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    
    # Эмоциональная окраска
    confidence_score: float  # 0-1, уверенность в ответе
    stress_indicators: List[str]  # индикаторы стресса
    emotional_tone: str  # neutral, positive, negative, stressed
    
    # Логическая структура
    coherence_score: float  # 0-1, связность изложения
    structure_score: float  # 0-1, структурированность ответа
    completeness_score: float  # 0-1, полнота ответа
    
    # Коммуникативные навыки
    clarity_score: float  # 0-1, ясность объяснений
    specificity_score: float  # 0-1, конкретность ответов
    examples_count: int  # количество примеров
    metrics_count: int  # количество метрик/цифр

@dataclass
class VacancyMatch:
    """Соответствие ответа требованиям вакансии."""
    requirement: str
    match_type: str  # confirmed, unconfirmed, contradiction, red_flag
    confidence: float  # 0-1, уверенность в сопоставлении
    evidence: List[str]  # доказательства соответствия
    gaps: List[str]  # пробелы или противоречия

@dataclass
class SoftSkillsAnalysis:
    """Анализ soft skills за интервью."""
    total_responses: int
    avg_response_duration: float
    total_pause_time: float
    pause_frequency: float  # пауз в минуту
    
    # Общие метрики
    avg_confidence: float
    avg_coherence: float
    avg_clarity: float
    avg_specificity: float
    
    # Эмоциональные паттерны
    dominant_emotional_tone: str
    stress_frequency: float
    confidence_trend: List[float]  # тренд уверенности по времени
    
    # Коммуникативные навыки
    communication_score: float  # 0-1
    critical_thinking_score: float  # 0-1
    teamwork_score: float  # 0-1
    adaptability_score: float  # 0-1
    
    # Соответствие вакансии
    technical_match_percentage: float
    communication_match_percentage: float
    experience_match_percentage: float
    overall_match_percentage: float
    
    # Проблемные паттерны
    contradictions: List[str]
    red_flags: List[str]
    template_responses: List[str]
    evasion_patterns: List[str]

class SoftSkillsAnalyzer:
    """Анализатор soft skills и поведенческих паттернов."""
    
    def __init__(self, vacancy_requirements: Dict[str, Any]):
        self.vacancy_requirements = vacancy_requirements
        self.response_history: List[ResponseMetrics] = []
        self.vacancy_matches: List[VacancyMatch] = []
        
        # Паттерны для анализа
        self.template_patterns = [
            r"всегда стремился к развитию",
            r"командный игрок",
            r"ответственный подход",
            r"высокая мотивация",
            r"готовность к обучению",
            r"стрессоустойчивость",
            r"коммуникабельность"
        ]
        
        self.stress_indicators = [
            r"эм\.\.\.", r"ну\.\.\.", r"как бы", r"в общем",
            r"не знаю", r"сложно сказать", r"трудно объяснить"
        ]
        
        self.confidence_indicators = [
            r"уверен", r"точно", r"определенно", r"конечно",
            r"безусловно", r"абсолютно", r"точно знаю"
        ]
        
        self.evasion_patterns = [
            r"это сложный вопрос", r"не могу точно сказать",
            r"зависит от ситуации", r"по-разному бывает"
        ]
        
        # Веса для расчета соответствия
        self.match_weights = {
            "technical_skills": 0.5,
            "communication": 0.3,
            "experience": 0.2
        }
        
        logger.info("SoftSkillsAnalyzer инициализирован")
    
    def analyze_response(self, 
                        question_id: str, 
                        response_text: str, 
                        response_duration: float,
                        pause_data: Optional[Dict[str, Any]] = None) -> ResponseMetrics:
        """Анализ одного ответа кандидата."""
        
        # Базовая статистика
        word_count = len(response_text.split())
        sentences = re.split(r'[.!?]+', response_text)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Анализ пауз
        pause_count = 0
        total_pause_duration = 0.0
        if pause_data:
            pause_count = pause_data.get("pause_count", 0)
            total_pause_duration = pause_data.get("total_pause_duration", 0.0)
        
        # Эмоциональная окраска
        confidence_score = self._calculate_confidence_score(response_text)
        stress_indicators = self._detect_stress_indicators(response_text)
        emotional_tone = self._determine_emotional_tone(response_text, stress_indicators)
        
        # Логическая структура
        coherence_score = self._calculate_coherence_score(response_text)
        structure_score = self._calculate_structure_score(response_text)
        completeness_score = self._calculate_completeness_score(response_text, question_id)
        
        # Коммуникативные навыки
        clarity_score = self._calculate_clarity_score(response_text)
        specificity_score = self._calculate_specificity_score(response_text)
        examples_count = self._count_examples(response_text)
        metrics_count = self._count_metrics(response_text)
        
        metrics = ResponseMetrics(
            timestamp=time.time(),
            question_id=question_id,
            response_text=response_text,
            response_duration=response_duration,
            pause_count=pause_count,
            total_pause_duration=total_pause_duration,
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=avg_sentence_length,
            confidence_score=confidence_score,
            stress_indicators=stress_indicators,
            emotional_tone=emotional_tone,
            coherence_score=coherence_score,
            structure_score=structure_score,
            completeness_score=completeness_score,
            clarity_score=clarity_score,
            specificity_score=specificity_score,
            examples_count=examples_count,
            metrics_count=metrics_count
        )
        
        self.response_history.append(metrics)
        logger.debug(f"Response analyzed: {question_id}, confidence={confidence_score:.2f}")
        
        return metrics
    
    def analyze_vacancy_match(self, response_text: str, question_context: str) -> List[VacancyMatch]:
        """Анализ соответствия ответа требованиям вакансии."""
        matches = []
        
        # Извлекаем требования из вакансии
        technical_requirements = self.vacancy_requirements.get("technical_skills", [])
        soft_requirements = self.vacancy_requirements.get("soft_skills", [])
        experience_requirements = self.vacancy_requirements.get("experience", [])
        
        # Анализ технических навыков
        for requirement in technical_requirements:
            match = self._match_technical_requirement(response_text, requirement)
            if match:
                matches.append(match)
        
        # Анализ soft skills
        for requirement in soft_requirements:
            match = self._match_soft_skill_requirement(response_text, requirement)
            if match:
                matches.append(match)
        
        # Анализ опыта
        for requirement in experience_requirements:
            match = self._match_experience_requirement(response_text, requirement)
            if match:
                matches.append(match)
        
        self.vacancy_matches.extend(matches)
        return matches
    
    def generate_soft_skills_analysis(self) -> SoftSkillsAnalysis:
        """Генерация комплексного анализа soft skills."""
        if not self.response_history:
            return self._create_empty_analysis()
        
        # Базовые метрики
        total_responses = len(self.response_history)
        avg_response_duration = np.mean([r.response_duration for r in self.response_history])
        total_pause_time = sum([r.total_pause_duration for r in self.response_history])
        pause_frequency = sum([r.pause_count for r in self.response_history]) / (avg_response_duration * total_responses / 60)
        
        # Средние показатели
        avg_confidence = np.mean([r.confidence_score for r in self.response_history])
        avg_coherence = np.mean([r.coherence_score for r in self.response_history])
        avg_clarity = np.mean([r.clarity_score for r in self.response_history])
        avg_specificity = np.mean([r.specificity_score for r in self.response_history])
        
        # Эмоциональные паттерны
        emotional_tones = [r.emotional_tone for r in self.response_history]
        dominant_emotional_tone = max(set(emotional_tones), key=emotional_tones.count)
        stress_frequency = len([r for r in self.response_history if r.emotional_tone == "stressed"]) / total_responses
        confidence_trend = [r.confidence_score for r in self.response_history]
        
        # Коммуникативные навыки
        communication_score = (avg_clarity + avg_coherence + avg_specificity) / 3
        critical_thinking_score = self._calculate_critical_thinking_score()
        teamwork_score = self._calculate_teamwork_score()
        adaptability_score = self._calculate_adaptability_score()
        
        # Соответствие вакансии
        technical_match = self._calculate_technical_match_percentage()
        communication_match = self._calculate_communication_match_percentage()
        experience_match = self._calculate_experience_match_percentage()
        overall_match = (
            technical_match * self.match_weights["technical_skills"] +
            communication_match * self.match_weights["communication"] +
            experience_match * self.match_weights["experience"]
        )
        
        # Проблемные паттерны
        contradictions = self._detect_contradictions()
        red_flags = self._detect_red_flags()
        template_responses = self._detect_template_responses()
        evasion_patterns = self._detect_evasion_patterns()
        
        return SoftSkillsAnalysis(
            total_responses=total_responses,
            avg_response_duration=avg_response_duration,
            total_pause_time=total_pause_time,
            pause_frequency=pause_frequency,
            avg_confidence=avg_confidence,
            avg_coherence=avg_coherence,
            avg_clarity=avg_clarity,
            avg_specificity=avg_specificity,
            dominant_emotional_tone=dominant_emotional_tone,
            stress_frequency=stress_frequency,
            confidence_trend=confidence_trend,
            communication_score=communication_score,
            critical_thinking_score=critical_thinking_score,
            teamwork_score=teamwork_score,
            adaptability_score=adaptability_score,
            technical_match_percentage=technical_match,
            communication_match_percentage=communication_match,
            experience_match_percentage=experience_match,
            overall_match_percentage=overall_match,
            contradictions=contradictions,
            red_flags=red_flags,
            template_responses=template_responses,
            evasion_patterns=evasion_patterns
        )
    
    def _calculate_confidence_score(self, text: str) -> float:
        """Расчет уверенности в ответе."""
        confidence_indicators = len(re.findall('|'.join(self.confidence_indicators), text.lower()))
        stress_indicators = len(re.findall('|'.join(self.stress_indicators), text.lower()))
        
        # Базовая уверенность
        base_confidence = 0.5
        
        # Корректировка на основе индикаторов
        confidence_adjustment = (confidence_indicators * 0.1) - (stress_indicators * 0.15)
        
        return max(0.0, min(1.0, base_confidence + confidence_adjustment))
    
    def _detect_stress_indicators(self, text: str) -> List[str]:
        """Детекция индикаторов стресса."""
        found_indicators = []
        for pattern in self.stress_indicators:
            if re.search(pattern, text.lower()):
                found_indicators.append(pattern)
        return found_indicators
    
    def _determine_emotional_tone(self, text: str, stress_indicators: List[str]) -> str:
        """Определение эмоционального тона."""
        if len(stress_indicators) > 2:
            return "stressed"
        
        positive_words = len(re.findall(r'хорошо|отлично|успешно|получилось|доволен', text.lower()))
        negative_words = len(re.findall(r'плохо|сложно|трудно|проблемы|неудачи', text.lower()))
        
        if positive_words > negative_words:
            return "positive"
        elif negative_words > positive_words:
            return "negative"
        else:
            return "neutral"
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Расчет связности изложения."""
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 2:
            return 1.0
        
        # Проверяем связующие слова
        connectors = len(re.findall(r'поэтому|следовательно|таким образом|кроме того|также|более того', text.lower()))
        
        # Проверяем логическую последовательность
        logical_score = min(1.0, connectors / (len(sentences) - 1))
        
        return logical_score
    
    def _calculate_structure_score(self, text: str) -> float:
        """Расчет структурированности ответа."""
        # Проверяем наличие структуры (введение, основная часть, заключение)
        structure_indicators = len(re.findall(r'во-первых|во-вторых|в итоге|в заключение|подводя итог', text.lower()))
        
        return min(1.0, structure_indicators / 3)
    
    def _calculate_completeness_score(self, text: str, question_id: str) -> float:
        """Расчет полноты ответа."""
        # Базовая полнота на основе длины ответа
        word_count = len(text.split())
        base_completeness = min(1.0, word_count / 50)  # 50 слов = полный ответ
        
        # Проверяем наличие примеров
        has_examples = bool(re.search(r'например|к примеру|в моем случае|когда я', text.lower()))
        example_bonus = 0.2 if has_examples else 0
        
        return min(1.0, base_completeness + example_bonus)
    
    def _calculate_clarity_score(self, text: str) -> float:
        """Расчет ясности объяснений."""
        # Проверяем простоту языка
        complex_words = len(re.findall(r'[а-я]{10,}', text.lower()))  # длинные слова
        total_words = len(text.split())
        
        complexity_ratio = complex_words / total_words if total_words > 0 else 0
        clarity_score = max(0.0, 1.0 - complexity_ratio)
        
        return clarity_score
    
    def _calculate_specificity_score(self, text: str) -> float:
        """Расчет конкретности ответов."""
        # Проверяем наличие конкретных деталей
        specific_indicators = len(re.findall(r'\d+%|\d+ лет|\d+ месяцев|\d+ человек|\d+ проектов', text.lower()))
        vague_indicators = len(re.findall(r'много|несколько|часто|иногда|обычно', text.lower()))
        
        specificity_score = min(1.0, specific_indicators / 3) - (vague_indicators * 0.1)
        return max(0.0, specificity_score)
    
    def _count_examples(self, text: str) -> int:
        """Подсчет количества примеров."""
        example_patterns = [
            r'например', r'к примеру', r'в моем случае', r'когда я',
            r'в проекте', r'на предыдущей работе', r'в команде'
        ]
        
        total_examples = 0
        for pattern in example_patterns:
            total_examples += len(re.findall(pattern, text.lower()))
        
        return total_examples
    
    def _count_metrics(self, text: str) -> int:
        """Подсчет количества метрик и цифр."""
        metrics_patterns = [
            r'\d+%', r'\d+ лет', r'\d+ месяцев', r'\d+ человек',
            r'\d+ проектов', r'\d+ раз', r'\d+ часов'
        ]
        
        total_metrics = 0
        for pattern in metrics_patterns:
            total_metrics += len(re.findall(pattern, text.lower()))
        
        return total_metrics
    
    def _match_technical_requirement(self, text: str, requirement: str) -> Optional[VacancyMatch]:
        """Сопоставление технического требования."""
        requirement_lower = requirement.lower()
        text_lower = text.lower()
        
        # Проверяем упоминание технологии
        if requirement_lower in text_lower:
            # Ищем подтверждающие детали
            evidence = []
            if re.search(r'\d+ лет.*' + requirement_lower, text_lower):
                evidence.append(f"Опыт работы: {requirement}")
            if re.search(r'проект.*' + requirement_lower, text_lower):
                evidence.append(f"Практическое применение: {requirement}")
            
            match_type = "confirmed" if evidence else "unconfirmed"
            confidence = 0.9 if evidence else 0.6
            
            return VacancyMatch(
                requirement=requirement,
                match_type=match_type,
                confidence=confidence,
                evidence=evidence,
                gaps=[]
            )
        
        return None
    
    def _match_soft_skill_requirement(self, text: str, requirement: str) -> Optional[VacancyMatch]:
        """Сопоставление soft skill требования."""
        requirement_lower = requirement.lower()
        text_lower = text.lower()
        
        # Словарь синонимов для soft skills
        skill_synonyms = {
            "коммуникабельность": ["общение", "команда", "взаимодействие"],
            "лидерство": ["руководство", "управление", "ведущий"],
            "адаптивность": ["адаптация", "изменения", "гибкость"],
            "критическое мышление": ["анализ", "решение проблем", "логика"]
        }
        
        # Проверяем прямое упоминание или синонимы
        keywords = [requirement_lower]
        if requirement_lower in skill_synonyms:
            keywords.extend(skill_synonyms[requirement_lower])
        
        found_keywords = []
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            # Ищем примеры применения навыка
            evidence = []
            if re.search(r'пример.*' + '|'.join(found_keywords), text_lower):
                evidence.append(f"Пример применения: {requirement}")
            
            match_type = "confirmed" if evidence else "unconfirmed"
            confidence = 0.8 if evidence else 0.5
            
            return VacancyMatch(
                requirement=requirement,
                match_type=match_type,
                confidence=confidence,
                evidence=evidence,
                gaps=[]
            )
        
        return None
    
    def _match_experience_requirement(self, text: str, requirement: str) -> Optional[VacancyMatch]:
        """Сопоставление требования по опыту."""
        text_lower = text.lower()
        
        # Ищем упоминания опыта работы
        experience_patterns = [
            r'\d+ лет.*опыт', r'\d+ лет.*работа', r'\d+ лет.*в сфере',
            r'опыт.*\d+ лет', r'работал.*\d+ лет'
        ]
        
        for pattern in experience_patterns:
            if re.search(pattern, text_lower):
                # Извлекаем количество лет
                years_match = re.search(r'(\d+)', text_lower)
                if years_match:
                    years = int(years_match.group(1))
                    
                    # Проверяем соответствие требованию
                    if "лет" in requirement.lower():
                        req_years_match = re.search(r'(\d+)', requirement.lower())
                        if req_years_match:
                            req_years = int(req_years_match.group(1))
                            
                            if years >= req_years:
                                return VacancyMatch(
                                    requirement=requirement,
                                    match_type="confirmed",
                                    confidence=0.9,
                                    evidence=[f"Опыт работы: {years} лет"],
                                    gaps=[]
                                )
                            else:
                                return VacancyMatch(
                                    requirement=requirement,
                                    match_type="contradiction",
                                    confidence=0.8,
                                    evidence=[],
                                    gaps=[f"Недостаточно опыта: {years} лет вместо {req_years}"]
                                )
        
        return None
    
    def _calculate_critical_thinking_score(self) -> float:
        """Расчет навыков критического мышления."""
        if not self.response_history:
            return 0.0
        
        total_score = 0.0
        for response in self.response_history:
            # Проверяем анализ проблем
            problem_analysis = len(re.findall(r'проблема|задача|вызов|сложность', response.response_text.lower()))
            solution_proposal = len(re.findall(r'решение|подход|метод|способ', response.response_text.lower()))
            
            thinking_score = min(1.0, (problem_analysis + solution_proposal) / 4)
            total_score += thinking_score
        
        return total_score / len(self.response_history)
    
    def _calculate_teamwork_score(self) -> float:
        """Расчет навыков работы в команде."""
        if not self.response_history:
            return 0.0
        
        total_score = 0.0
        for response in self.response_history:
            # Проверяем упоминания командной работы
            team_indicators = len(re.findall(r'команда|коллеги|совместно|вместе|группа', response.response_text.lower()))
            collaboration_score = min(1.0, team_indicators / 3)
            total_score += collaboration_score
        
        return total_score / len(self.response_history)
    
    def _calculate_adaptability_score(self) -> float:
        """Расчет адаптивности."""
        if not self.response_history:
            return 0.0
        
        # Анализируем тренд уверенности
        confidence_trend = [r.confidence_score for r in self.response_history]
        if len(confidence_trend) > 1:
            # Проверяем, растет ли уверенность (адаптация к процессу)
            trend_slope = np.polyfit(range(len(confidence_trend)), confidence_trend, 1)[0]
            adaptability_score = max(0.0, min(1.0, trend_slope + 0.5))
        else:
            adaptability_score = 0.5
        
        return adaptability_score
    
    def _calculate_technical_match_percentage(self) -> float:
        """Расчет процентного соответствия техническим навыкам."""
        technical_matches = [m for m in self.vacancy_matches if "технический" in m.requirement.lower()]
        if not technical_matches:
            return 0.0
        
        confirmed_matches = len([m for m in technical_matches if m.match_type == "confirmed"])
        return (confirmed_matches / len(technical_matches)) * 100
    
    def _calculate_communication_match_percentage(self) -> float:
        """Расчет процентного соответствия коммуникативным навыкам."""
        communication_matches = [m for m in self.vacancy_matches if any(skill in m.requirement.lower() for skill in ["коммуникация", "общение", "команда"])]
        if not communication_matches:
            return 0.0
        
        confirmed_matches = len([m for m in communication_matches if m.match_type == "confirmed"])
        return (confirmed_matches / len(communication_matches)) * 100
    
    def _calculate_experience_match_percentage(self) -> float:
        """Расчет процентного соответствия требованиям по опыту."""
        experience_matches = [m for m in self.vacancy_matches if "опыт" in m.requirement.lower() or "лет" in m.requirement.lower()]
        if not experience_matches:
            return 0.0
        
        confirmed_matches = len([m for m in experience_matches if m.match_type == "confirmed"])
        return (confirmed_matches / len(experience_matches)) * 100
    
    def _detect_contradictions(self) -> List[str]:
        """Детекция противоречий в ответах."""
        contradictions = []
        
        # Проверяем противоречия в опыте работы
        experience_claims = []
        for response in self.response_history:
            experience_matches = re.findall(r'(\d+) лет.*опыт', response.response_text.lower())
            experience_claims.extend(experience_matches)
        
        if len(set(experience_claims)) > 1:
            contradictions.append(f"Противоречия в опыте работы: {', '.join(set(experience_claims))} лет")
        
        return contradictions
    
    def _detect_red_flags(self) -> List[str]:
        """Детекция красных флагов."""
        red_flags = []
        
        for response in self.response_history:
            # Агрессивность
            if response.emotional_tone == "negative" and response.confidence_score < 0.3:
                red_flags.append("Агрессивная реакция на вопросы")
            
            # Уклонение
            if response.specificity_score < 0.3 and response.examples_count == 0:
                red_flags.append("Уклонение от конкретных ответов")
            
            # Шаблонность
            if response.examples_count == 0 and response.metrics_count == 0:
                red_flags.append("Шаблонные ответы без примеров")
        
        return red_flags
    
    def _detect_template_responses(self) -> List[str]:
        """Детекция шаблонных ответов."""
        template_responses = []
        
        for response in self.response_history:
            for pattern in self.template_patterns:
                if re.search(pattern, response.response_text.lower()):
                    template_responses.append(f"Шаблонная фраза: '{pattern}'")
        
        return template_responses
    
    def _detect_evasion_patterns(self) -> List[str]:
        """Детекция паттернов уклонения."""
        evasion_patterns = []
        
        for response in self.response_history:
            for pattern in self.evasion_patterns:
                if re.search(pattern, response.response_text.lower()):
                    evasion_patterns.append(f"Уклонение: '{pattern}'")
        
        return evasion_patterns
    
    def _create_empty_analysis(self) -> SoftSkillsAnalysis:
        """Создание пустого анализа."""
        return SoftSkillsAnalysis(
            total_responses=0,
            avg_response_duration=0.0,
            total_pause_time=0.0,
            pause_frequency=0.0,
            avg_confidence=0.0,
            avg_coherence=0.0,
            avg_clarity=0.0,
            avg_specificity=0.0,
            dominant_emotional_tone="neutral",
            stress_frequency=0.0,
            confidence_trend=[],
            communication_score=0.0,
            critical_thinking_score=0.0,
            teamwork_score=0.0,
            adaptability_score=0.0,
            technical_match_percentage=0.0,
            communication_match_percentage=0.0,
            experience_match_percentage=0.0,
            overall_match_percentage=0.0,
            contradictions=[],
            red_flags=[],
            template_responses=[],
            evasion_patterns=[]
        )

def create_soft_skills_analyzer(vacancy_requirements: Dict[str, Any]) -> SoftSkillsAnalyzer:
    """Создание анализатора soft skills."""
    return SoftSkillsAnalyzer(vacancy_requirements)
