"""Add AI models configuration tables

Revision ID: add_ai_models_tables
Revises: ea52454e6a30
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from typing import Union

# revision identifiers, used by Alembic.
revision = 'add_ai_models_tables'
down_revision: Union[str, None] = 'ea52454e6a30'
branch_labels = None
depends_on = None

def upgrade():
    """Создание таблиц для настройки AI моделей."""
    
    # Создание enum типов
    model_type_enum = postgresql.ENUM(
        'llm', 'stt', 'tts', 'avatar', 'vision',
        name='modeltypeenum',
        create_type=False
    )
    model_type_enum.create(op.get_bind(), checkfirst=True)
    
    model_provider_enum = postgresql.ENUM(
        # API провайдеры
        'openai', 'groq', 'anthropic', 'cartesia', 'huggingface', 'replicate', 'cohere',
        # Локальные провайдеры
        'local_oollama', 'local_whisper', 'local_coqui', 'local_bark', 
        'local_vllm', 'local_ollamacpp', 'local_transformers', 'local_onnx', 'local_tensorrt',
        # Avatar провайдеры
        'simli',
        # Vision провайдеры
        'google_gemini', 'openai_vision', 'anthropic_vision', 'azure_vision',
        # Локальные Vision провайдеры
        'local_llava', 'local_cogvlm', 'local_blip2', 'local_instructblip', 
        'local_minigpt4', 'local_qwen_vl', 'local_internvl', 'local_moondream', 'local_bakllava',
        # Кастомные и универсальные
        'custom_endpoint', 'custom_local', 'openai_compatible',
        name='modelproviderenum',
        create_type=False
    )
    model_provider_enum.create(op.get_bind(), checkfirst=True)
    
    # Создание таблицы ai_model_configurations
    op.create_table(
        'ai_model_configurations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_type', model_type_enum, nullable=False, index=True),
        sa.Column('provider', model_provider_enum, nullable=False, index=True),
        sa.Column('model_name', sa.String(200), nullable=False),
        sa.Column('endpoint_url', sa.String(500), nullable=True),
        sa.Column('api_key_name', sa.String(100), nullable=True),
        sa.Column('model_path', sa.String(500), nullable=True),
        sa.Column('engine_path', sa.String(500), nullable=True),
        sa.Column('context_length', sa.Integer(), nullable=True),
        sa.Column('face_id', sa.String(100), nullable=True),
        sa.Column('max_session_length', sa.Integer(), nullable=True),
        sa.Column('max_idle_time', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True, default=0.7),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('timeout', sa.Integer(), nullable=True, default=30),
        sa.Column('extra_params', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Создание таблицы interview_model_configurations
    op.create_table(
        'interview_model_configurations',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('vacancy_id', sa.Integer(), sa.ForeignKey('vacancies.id'), nullable=False, index=True),
        sa.Column('llm_model_id', sa.Integer(), sa.ForeignKey('ai_model_configurations.id'), nullable=True),
        sa.Column('stt_model_id', sa.Integer(), sa.ForeignKey('ai_model_configurations.id'), nullable=True),
        sa.Column('tts_model_id', sa.Integer(), sa.ForeignKey('ai_model_configurations.id'), nullable=True),
        sa.Column('avatar_model_id', sa.Integer(), sa.ForeignKey('ai_model_configurations.id'), nullable=True),
        sa.Column('vision_model_id', sa.Integer(), sa.ForeignKey('ai_model_configurations.id'), nullable=True),
        sa.Column('max_questions', sa.Integer(), default=12),
        sa.Column('interview_timeout', sa.Integer(), default=3600),
        sa.Column('use_voice_activity_detection', sa.Boolean(), default=True),
        sa.Column('use_turn_detection', sa.Boolean(), default=True),
        sa.Column('silence_threshold', sa.Float(), default=0.5),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Создание таблицы model_usage_logs
    op.create_table(
        'model_usage_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('interview_config_id', sa.Integer(), sa.ForeignKey('interview_model_configurations.id'), nullable=False),
        sa.Column('ai_model_id', sa.Integer(), sa.ForeignKey('ai_model_configurations.id'), nullable=False),
        sa.Column('vacancy_id', sa.Integer(), sa.ForeignKey('vacancies.id'), nullable=False),
        sa.Column('applicant_id', sa.Integer(), sa.ForeignKey('applicant_profiles.id'), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('request_count', sa.Integer(), default=1),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime(), nullable=True)
    )
    
    # Создание индексов
    op.create_index('idx_ai_models_type_provider', 'ai_model_configurations', ['model_type', 'provider'])
    op.create_index('idx_ai_models_active_default', 'ai_model_configurations', ['is_active', 'is_default'])
    op.create_index('idx_interview_configs_vacancy', 'interview_model_configurations', ['vacancy_id', 'is_active'])
    op.create_index('idx_usage_logs_vacancy_applicant', 'model_usage_logs', ['vacancy_id', 'applicant_id'])
    op.create_index('idx_usage_logs_session', 'model_usage_logs', ['session_id'])
    op.create_index('idx_usage_logs_started_at', 'model_usage_logs', ['started_at'])


def downgrade():
    """Удаление таблиц AI моделей."""
    
    # Удаление индексов
    op.drop_index('idx_usage_logs_started_at')
    op.drop_index('idx_usage_logs_session')
    op.drop_index('idx_usage_logs_vacancy_applicant')
    op.drop_index('idx_interview_configs_vacancy')
    op.drop_index('idx_ai_models_active_default')
    op.drop_index('idx_ai_models_type_provider')
    
    # Удаление таблиц
    op.drop_table('model_usage_logs')
    op.drop_table('interview_model_configurations')
    op.drop_table('ai_model_configurations')
    
    # Удаление enum типов
    model_provider_enum = postgresql.ENUM(name='modelproviderenum')
    model_provider_enum.drop(op.get_bind(), checkfirst=True)
    
    model_type_enum = postgresql.ENUM(name='modeltypeenum')
    model_type_enum.drop(op.get_bind(), checkfirst=True)


def insert_default_models():
    """
    Вставка моделей по умолчанию.
    Вызывается отдельно после миграции или при инициализации приложения.
    """
    
    # Данные для вставки моделей по умолчанию
    default_models = [
        # LLM модели
        {
            'name': 'Groq qwen3-32b 8x7B',
            'description': 'Быстрая и качественная модель для интервью',
            'model_type': 'llm',
            'provider': 'groq',
            'model_name': 'qwen3-32b',
            'api_key_name': 'GROQ_API_KEY',
            'temperature': 0.7,
            'max_tokens': 4000,
            'is_default': True
        },
        {
            'name': 'OpenAI GPT-4',
            'description': 'Премиум модель для сложных интервью',
            'model_type': 'llm',
            'provider': 'openai',
            'model_name': 'gpt-4',
            'api_key_name': 'OPENAI_API_KEY',
            'temperature': 0.7,
            'max_tokens': 3000,
            'is_default': False
        },
        {
            'name': 'Local Oollama ollama3',
            'description': 'Локальная модель для конфиденциальных интервью',
            'model_type': 'llm',
            'provider': 'local_oollama',
            'model_name': 'ollama3:8b',
            'endpoint_url': 'http://localhost:11434',
            'temperature': 0.7,
            'is_default': False
        },
        
        # STT модели
        {
            'name': 'Groq Whisper Large',
            'description': 'Быстрое распознавание речи через API',
            'model_type': 'stt',
            'provider': 'groq',
            'model_name': 'whisper-large-v3',
            'api_key_name': 'GROQ_API_KEY',
            'is_default': True
        },
        {
            'name': 'OpenAI Whisper',
            'description': 'Высококачественное распознавание речи',
            'model_type': 'stt',
            'provider': 'openai',
            'model_name': 'whisper-1',
            'api_key_name': 'OPENAI_API_KEY',
            'is_default': False
        },
        {
            'name': 'Local Whisper',
            'description': 'Локальное распознавание речи',
            'model_type': 'stt',
            'provider': 'local_whisper',
            'model_name': 'openai/whisper-large-v3',
            'endpoint_url': 'http://localhost:8000',
            'is_default': False
        },
        
        # TTS модели
        {
            'name': 'Cartesia Sonic',
            'description': 'Быстрый и качественный синтез речи',
            'model_type': 'tts',
            'provider': 'cartesia',
            'model_name': 'sonic-english',
            'api_key_name': 'CARTESIA_API_KEY',
            'is_default': True
        },
        {
            'name': 'OpenAI TTS',
            'description': 'Высококачественный синтез речи',
            'model_type': 'tts',
            'provider': 'openai',
            'model_name': 'tts-1',
            'api_key_name': 'OPENAI_API_KEY',
            'is_default': False
        },
        {
            'name': 'Local Coqui TTS',
            'description': 'Локальный синтез речи',
            'model_type': 'tts',
            'provider': 'local_coqui',
            'model_name': 'tts_models/en/ljspeech/tacotron2-DDC',
            'endpoint_url': 'http://localhost:5002',
            'is_default': False
        }
    ]
    
    # SQL для вставки
    insert_sql = """
    INSERT INTO ai_model_configurations (
        name, description, model_type, provider, model_name,
        api_key_name, endpoint_url, temperature, max_tokens, is_default
    ) VALUES (
        %(name)s, %(description)s, %(model_type)s, %(provider)s, %(model_name)s,
        %(api_key_name)s, %(endpoint_url)s, %(temperature)s, %(max_tokens)s, %(is_default)s
    )
    """
    
    # Выполнение вставки
    connection = op.get_bind()
    for model_data in default_models:
        connection.execute(sa.text(insert_sql), model_data)


# Скрипт для инициализации моделей по умолчанию
if __name__ == "__main__":
    print("Для инициализации моделей по умолчанию выполните:")
    print("from backend.src.ml.videosdk.model_service import ModelConfigurationService")
    print("service = ModelConfigurationService()")
    print("service.initialize_default_models()")
