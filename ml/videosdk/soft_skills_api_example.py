"""
API для тестирования Soft Skills Analyzer.

Демонстрирует возможности анализа поведенческих паттернов,
фиксации пауз, эмоциональной окраски и NLP сопоставления с вакансией.
"""

from fastapi import FastAPI, HTTPException
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import time

# Импорты из нашего проекта
from .soft_skills_analyzer import (
    create_soft_skills_analyzer,
    SoftSkillsAnalyzer,
    ResponseMetrics,
    VacancyMatch,
    SoftSkillsAnalysis
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Soft Skills Analysis API",
    description="API для анализа soft skills и поведенческих паттернов",
    version="1.0.0"
)

# Pydantic модели для API

class VacancyRequirementsRequest(BaseModel):
    """Запрос на создание требований вакансии."""
    technical_skills: List[str] = Field(..., description="Список технических навыков")
    soft_skills: List[str] = Field(..., description="Список soft skills")
    experience: List[str] = Field(..., description="Требования по опыту")

class ResponseAnalysisRequest(BaseModel):
    """Запрос на анализ ответа."""
    question_id: str = Field(..., description="ID вопроса")
    response_text: str = Field(..., description="Текст ответа кандидата")
    response_duration: float = Field(..., description="Длительность ответа в секундах")
    pause_data: Optional[Dict[str, Any]] = Field(None, description="Данные о паузах")

class ResponseMetricsResponse(BaseModel):
    """Ответ с метриками ответа."""
    timestamp: float
    question_id: str
    response_duration: float
    pause_count: int
    total_pause_duration: float
    word_count: int
    sentence_count: int
    avg_sentence_length: float
    confidence_score: float
    stress_indicators: List[str]
    emotional_tone: str
    coherence_score: float
    structure_score: float
    completeness_score: float
    clarity_score: float
    specificity_score: float
    examples_count: int
    metrics_count: int

class VacancyMatchResponse(BaseModel):
    """Ответ с соответствием вакансии."""
    requirement: str
    match_type: str
    confidence: float
    evidence: List[str]
    gaps: List[str]

class ResponseAnalysisResponse(BaseModel):
    """Ответ анализа ответа."""
    success: bool
    response_metrics: Optional[ResponseMetricsResponse] = None
    vacancy_matches: Optional[List[VacancyMatchResponse]] = None
    error: Optional[str] = None

class SoftSkillsAnalysisResponse(BaseModel):
    """Ответ анализа soft skills."""
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class VacancyMatchSummaryResponse(BaseModel):
    """Ответ сводки соответствия вакансии."""
    success: bool
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Глобальные переменные
soft_skills_analyzer: Optional[SoftSkillsAnalyzer] = None

@app.post("/soft-skills/initialize")
async def initialize_soft_skills_analyzer(requirements: VacancyRequirementsRequest):
    """Инициализация анализатора soft skills."""
    global soft_skills_analyzer
    
    try:
        vacancy_requirements = {
            "technical_skills": requirements.technical_skills,
            "soft_skills": requirements.soft_skills,
            "experience": requirements.experience
        }
        
        soft_skills_analyzer = create_soft_skills_analyzer(vacancy_requirements)
        
        logger.info(f"Soft Skills Analyzer инициализирован с {len(requirements.technical_skills)} техническими навыками")
        
        return {
            "success": True,
            "message": "Soft Skills Analyzer инициализирован",
            "requirements_count": {
                "technical_skills": len(requirements.technical_skills),
                "soft_skills": len(requirements.soft_skills),
                "experience": len(requirements.experience)
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка инициализации Soft Skills Analyzer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/soft-skills/analyze-response", response_model=ResponseAnalysisResponse)
async def analyze_response(request: ResponseAnalysisRequest):
    """Анализ ответа кандидата."""
    if not soft_skills_analyzer:
        raise HTTPException(status_code=400, detail="Soft Skills Analyzer не инициализирован")
    
    try:
        # Анализируем ответ
        response_metrics = soft_skills_analyzer.analyze_response(
            question_id=request.question_id,
            response_text=request.response_text,
            response_duration=request.response_duration,
            pause_data=request.pause_data
        )
        
        # Анализируем соответствие вакансии
        vacancy_matches = soft_skills_analyzer.analyze_vacancy_match(
            response_text=request.response_text,
            question_context=request.question_id
        )
        
        # Конвертируем в response модели
        response_metrics_dict = ResponseMetricsResponse(
            timestamp=response_metrics.timestamp,
            question_id=response_metrics.question_id,
            response_duration=response_metrics.response_duration,
            pause_count=response_metrics.pause_count,
            total_pause_duration=response_metrics.total_pause_duration,
            word_count=response_metrics.word_count,
            sentence_count=response_metrics.sentence_count,
            avg_sentence_length=response_metrics.avg_sentence_length,
            confidence_score=response_metrics.confidence_score,
            stress_indicators=response_metrics.stress_indicators,
            emotional_tone=response_metrics.emotional_tone,
            coherence_score=response_metrics.coherence_score,
            structure_score=response_metrics.structure_score,
            completeness_score=response_metrics.completeness_score,
            clarity_score=response_metrics.clarity_score,
            specificity_score=response_metrics.specificity_score,
            examples_count=response_metrics.examples_count,
            metrics_count=response_metrics.metrics_count
        )
        
        vacancy_matches_dict = [
            VacancyMatchResponse(
                requirement=match.requirement,
                match_type=match.match_type,
                confidence=match.confidence,
                evidence=match.evidence,
                gaps=match.gaps
            ) for match in vacancy_matches
        ]
        
        logger.info(f"Response analyzed: {request.question_id}, confidence={response_metrics.confidence_score:.2f}")
        
        return ResponseAnalysisResponse(
            success=True,
            response_metrics=response_metrics_dict,
            vacancy_matches=vacancy_matches_dict
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа ответа: {e}")
        return ResponseAnalysisResponse(
            success=False,
            error=str(e)
        )

@app.get("/soft-skills/analysis", response_model=SoftSkillsAnalysisResponse)
async def get_soft_skills_analysis():
    """Получение комплексного анализа soft skills."""
    if not soft_skills_analyzer:
        raise HTTPException(status_code=400, detail="Soft Skills Analyzer не инициализирован")
    
    try:
        analysis = soft_skills_analyzer.generate_soft_skills_analysis()
        
        analysis_dict = {
            "total_responses": analysis.total_responses,
            "avg_response_duration": analysis.avg_response_duration,
            "pause_frequency": analysis.pause_frequency,
            
            # Общие метрики
            "avg_confidence": analysis.avg_confidence,
            "avg_coherence": analysis.avg_coherence,
            "avg_clarity": analysis.avg_clarity,
            "avg_specificity": analysis.avg_specificity,
            
            # Эмоциональные паттерны
            "dominant_emotional_tone": analysis.dominant_emotional_tone,
            "stress_frequency": analysis.stress_frequency,
            "confidence_trend": analysis.confidence_trend,
            
            # Коммуникативные навыки
            "communication_score": analysis.communication_score,
            "critical_thinking_score": analysis.critical_thinking_score,
            "teamwork_score": analysis.teamwork_score,
            "adaptability_score": analysis.adaptability_score,
            
            # Соответствие вакансии
            "technical_match_percentage": analysis.technical_match_percentage,
            "communication_match_percentage": analysis.communication_match_percentage,
            "experience_match_percentage": analysis.experience_match_percentage,
            "overall_match_percentage": analysis.overall_match_percentage,
            
            # Проблемные паттерны
            "contradictions": analysis.contradictions,
            "red_flags": analysis.red_flags,
            "template_responses": analysis.template_responses,
            "evasion_patterns": analysis.evasion_patterns
        }
        
        return SoftSkillsAnalysisResponse(
            success=True,
            analysis=analysis_dict
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения анализа soft skills: {e}")
        return SoftSkillsAnalysisResponse(
            success=False,
            error=str(e)
        )

@app.get("/soft-skills/vacancy-match", response_model=VacancyMatchSummaryResponse)
async def get_vacancy_match_summary():
    """Получение сводки соответствия вакансии."""
    if not soft_skills_analyzer:
        raise HTTPException(status_code=400, detail="Soft Skills Analyzer не инициализирован")
    
    try:
        matches = soft_skills_analyzer.vacancy_matches
        
        # Группируем по типам соответствия
        confirmed_matches = [m for m in matches if m.match_type == "confirmed"]
        unconfirmed_matches = [m for m in matches if m.match_type == "unconfirmed"]
        contradictions = [m for m in matches if m.match_type == "contradiction"]
        red_flags = [m for m in matches if m.match_type == "red_flag"]
        
        summary_dict = {
            "total_requirements": len(matches),
            "confirmed_matches": len(confirmed_matches),
            "unconfirmed_matches": len(unconfirmed_matches),
            "contradictions": len(contradictions),
            "red_flags": len(red_flags),
            
            "match_percentage": (len(confirmed_matches) / len(matches) * 100) if matches else 0,
            
            "confirmed_details": [
                {
                    "requirement": m.requirement,
                    "confidence": m.confidence,
                    "evidence": m.evidence
                } for m in confirmed_matches
            ],
            
            "unconfirmed_details": [
                {
                    "requirement": m.requirement,
                    "confidence": m.confidence,
                    "gaps": m.gaps
                } for m in unconfirmed_matches
            ],
            
            "contradictions_details": [
                {
                    "requirement": m.requirement,
                    "confidence": m.confidence,
                    "gaps": m.gaps
                } for m in contradictions
            ],
            
            "red_flags_details": [
                {
                    "requirement": m.requirement,
                    "confidence": m.confidence,
                    "gaps": m.gaps
                } for m in red_flags
            ]
        }
        
        return VacancyMatchSummaryResponse(
            success=True,
            summary=summary_dict
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения сводки соответствия: {e}")
        return VacancyMatchSummaryResponse(
            success=False,
            error=str(e)
        )

@app.post("/soft-skills/reset")
async def reset_analysis():
    """Сброс анализа (очистка истории)."""
    if not soft_skills_analyzer:
        raise HTTPException(status_code=400, detail="Soft Skills Analyzer не инициализирован")
    
    try:
        soft_skills_analyzer.response_history.clear()
        soft_skills_analyzer.vacancy_matches.clear()
        
        logger.info("Анализ сброшен")
        
        return {
            "success": True,
            "message": "Анализ сброшен"
        }
        
    except Exception as e:
        logger.error(f"Ошибка сброса анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/soft-skills/demo")
async def get_demo_info():
    """Получить информацию о демо возможностях."""
    return {
        "title": "Soft Skills Analysis Demo API",
        "description": "Анализ поведенческих паттернов и соответствия вакансии",
        "features": [
            "Фиксация пауз и эмоциональной окраски ответов",
            "Анализ логической структуры и коммуникативных навыков",
            "NLP сопоставление с требованиями вакансии",
            "Выявление подтвержденных/неподтвержденных пунктов",
            "Расчет процентного соответствия с настраиваемыми весами",
            "Детекция противоречий и красных флагов",
            "Анализ шаблонных ответов и уклонений"
        ],
        "endpoints": {
            "initialize": "POST /soft-skills/initialize - Инициализация анализатора",
            "analyze_response": "POST /soft-skills/analyze-response - Анализ ответа",
            "get_analysis": "GET /soft-skills/analysis - Комплексный анализ",
            "get_vacancy_match": "GET /soft-skills/vacancy-match - Соответствие вакансии",
            "reset": "POST /soft-skills/reset - Сброс анализа"
        },
        "usage_example": {
            "step1": "POST /soft-skills/initialize - Инициализировать анализатор",
            "step2": "POST /soft-skills/analyze-response - Анализировать ответы",
            "step3": "GET /soft-skills/analysis - Получить комплексный анализ",
            "step4": "GET /soft-skills/vacancy-match - Проверить соответствие вакансии"
        },
        "analysis_metrics": {
            "response_metrics": [
                "confidence_score - уверенность в ответе",
                "emotional_tone - эмоциональный тон",
                "coherence_score - связность изложения",
                "clarity_score - ясность объяснений",
                "specificity_score - конкретность ответов"
            ],
            "soft_skills": [
                "communication_score - коммуникативные навыки",
                "critical_thinking_score - критическое мышление",
                "teamwork_score - работа в команде",
                "adaptability_score - адаптивность"
            ],
            "vacancy_matching": [
                "technical_match_percentage - соответствие техническим навыкам",
                "communication_match_percentage - соответствие коммуникации",
                "experience_match_percentage - соответствие опыту",
                "overall_match_percentage - общее соответствие"
            ]
        },
        "problematic_patterns": {
            "contradictions": "Противоречия в ответах",
            "red_flags": "Красные флаги (агрессия, уклонение)",
            "template_responses": "Шаблонные ответы",
            "evasion_patterns": "Паттерны уклонения"
        }
    }

@app.get("/health/soft-skills")
async def check_soft_skills_health():
    """Проверка состояния soft skills системы."""
    try:
        health_status = {
            "status": "healthy",
            "checks": []
        }
        
        # Проверка анализатора
        if soft_skills_analyzer:
            health_status["checks"].append({
                "name": "Soft Skills Analyzer",
                "status": "pass",
                "details": f"Initialized, {len(soft_skills_analyzer.response_history)} responses analyzed"
            })
        else:
            health_status["checks"].append({
                "name": "Soft Skills Analyzer",
                "status": "fail",
                "details": "Not initialized"
            })
            health_status["status"] = "unhealthy"
        
        # Проверка numpy
        try:
            import numpy as np
            health_status["checks"].append({
                "name": "NumPy",
                "status": "pass",
                "details": "Available"
            })
        except ImportError:
            health_status["checks"].append({
                "name": "NumPy",
                "status": "fail",
                "details": "NumPy not installed"
            })
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Soft skills health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checks": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
