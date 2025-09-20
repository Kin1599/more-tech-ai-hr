/**
 * AvatarMeetingIntegration - Интеграция AI аватара в VideoSDK meeting.
 * 
 * Управляет отображением AI аватара поверх видео участников,
 * синхронизацией с речью и face tracking данными.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import AvatarOverlay from './AvatarOverlay';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';

const AvatarMeetingIntegration = ({ 
  meeting, 
  participantId, 
  onAvatarStatusChange = () => {},
  className = ""
}) => {
  const [avatarActive, setAvatarActive] = useState(false);
  const [avatarConfig, setAvatarConfig] = useState({
    resolution: [640, 480],
    fps: 30,
    faceId: 'default_face',
    talkingSensitivity: 0.3,
    emotionDetection: true,
    headMovementEnabled: true,
    eyeBlinkEnabled: true,
    backgroundColor: [50, 50, 50],
    avatarScale: 0.8
  });
  const [avatarStatus, setAvatarStatus] = useState({
    isTalking: false,
    emotion: 'neutral',
    mouthOpenness: 0,
    eyeBlink: false,
    headMovement: { x: 0, y: 0, z: 0 },
    speechIntensity: 0
  });
  const [faceTrackingData, setFaceTrackingData] = useState(null);
  const [speechData, setSpeechData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const lastUpdateTimeRef = useRef(0);

  useEffect(() => {
    if (avatarActive && meeting) {
      initializeAvatarIntegration();
    } else {
      cleanupAvatarIntegration();
    }

    return () => {
      cleanupAvatarIntegration();
    };
  }, [avatarActive, meeting]);

  useEffect(() => {
    if (avatarActive) {
      startAudioAnalysis();
    } else {
      stopAudioAnalysis();
    }

    return () => {
      stopAudioAnalysis();
    };
  }, [avatarActive]);

  useEffect(() => {
    // Уведомляем родительский компонент об изменении статуса аватара
    onAvatarStatusChange({
      active: avatarActive,
      status: avatarStatus,
      config: avatarConfig
    });
  }, [avatarActive, avatarStatus, avatarConfig, onAvatarStatusChange]);

  const initializeAvatarIntegration = async () => {
    try {
      setConnectionStatus('connecting');
      
      // Инициализируем аудио контекст для анализа речи
      await initializeAudioContext();
      
      // Подписываемся на события meeting
      setupMeetingEventListeners();
      
      // Запускаем avatar stream
      await startAvatarStream();
      
      setConnectionStatus('connected');
      console.log('Avatar integration initialized');
      
    } catch (error) {
      console.error('Error initializing avatar integration:', error);
      setConnectionStatus('error');
    }
  };

  const cleanupAvatarIntegration = () => {
    stopAudioAnalysis();
    removeMeetingEventListeners();
    stopAvatarStream();
    setConnectionStatus('disconnected');
  };

  const initializeAudioContext = async () => {
    try {
      // Создаем AudioContext для анализа аудио
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      
      // Создаем AnalyserNode для анализа частот
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      analyserRef.current.smoothingTimeConstant = 0.8;
      
      console.log('Audio context initialized');
    } catch (error) {
      console.error('Error initializing audio context:', error);
    }
  };

  const setupMeetingEventListeners = () => {
    if (!meeting) return;

    // Слушаем события участников
    meeting.on('participantJoined', handleParticipantJoined);
    meeting.on('participantLeft', handleParticipantLeft);
    
    // Слушаем события потоков
    meeting.on('streamEnabled', handleStreamEnabled);
    meeting.on('streamDisabled', handleStreamDisabled);
    
    // Слушаем события микрофона
    meeting.on('micEnabled', handleMicEnabled);
    meeting.on('micDisabled', handleMicDisabled);
  };

  const removeMeetingEventListeners = () => {
    if (!meeting) return;

    meeting.off('participantJoined', handleParticipantJoined);
    meeting.off('participantLeft', handleParticipantLeft);
    meeting.off('streamEnabled', handleStreamEnabled);
    meeting.off('streamDisabled', handleStreamDisabled);
    meeting.off('micEnabled', handleMicEnabled);
    meeting.off('micDisabled', handleMicDisabled);
  };

  const handleParticipantJoined = (participant) => {
    console.log('Participant joined:', participant.id);
    
    // Если это наш участник, начинаем отслеживание
    if (participant.id === participantId) {
      startParticipantTracking(participant);
    }
  };

  const handleParticipantLeft = (participant) => {
    console.log('Participant left:', participant.id);
    
    if (participant.id === participantId) {
      stopParticipantTracking();
    }
  };

  const handleStreamEnabled = (stream) => {
    console.log('Stream enabled:', stream.kind, stream.participantId);
    
    if (stream.participantId === participantId && stream.kind === 'video') {
      // Начинаем face tracking для видео потока
      startFaceTracking(stream);
    }
  };

  const handleStreamDisabled = (stream) => {
    console.log('Stream disabled:', stream.kind, stream.participantId);
    
    if (stream.participantId === participantId && stream.kind === 'video') {
      stopFaceTracking();
    }
  };

  const handleMicEnabled = () => {
    console.log('Microphone enabled');
    startSpeechAnalysis();
  };

  const handleMicDisabled = () => {
    console.log('Microphone disabled');
    stopSpeechAnalysis();
  };

  const startParticipantTracking = (participant) => {
    // Начинаем отслеживание участника
    console.log('Starting participant tracking for:', participant.id);
  };

  const stopParticipantTracking = () => {
    // Останавливаем отслеживание участника
    console.log('Stopping participant tracking');
  };

  const startFaceTracking = (videoStream) => {
    // Начинаем face tracking для видео потока
    console.log('Starting face tracking for video stream');
    
    // Здесь должна быть интеграция с face tracking API
    // Пока имитируем данные
    simulateFaceTrackingData();
  };

  const stopFaceTracking = () => {
    // Останавливаем face tracking
    console.log('Stopping face tracking');
    setFaceTrackingData(null);
  };

  const simulateFaceTrackingData = () => {
    const updateFaceData = () => {
      if (avatarActive) {
        const faceData = {
          faceDetected: Math.random() > 0.1, // 90% времени лицо в кадре
          faceConfidence: 0.7 + Math.random() * 0.3,
          gazeDirection: {
            x: (Math.random() - 0.5) * 20, // -10 до 10 градусов
            y: (Math.random() - 0.5) * 15  // -7.5 до 7.5 градусов
          },
          headPose: {
            yaw: (Math.random() - 0.5) * 10,
            pitch: (Math.random() - 0.5) * 8,
            roll: (Math.random() - 0.5) * 5
          },
          eyeBlink: Math.random() < 0.01 // 1% шанс моргнуть
        };
        
        setFaceTrackingData(faceData);
        
        // Обновляем статус аватара на основе face tracking
        updateAvatarFromFaceTracking(faceData);
        
        requestAnimationFrame(updateFaceData);
      }
    };
    
    updateFaceData();
  };

  const updateAvatarFromFaceTracking = (faceData) => {
    setAvatarStatus(prev => ({
      ...prev,
      eyeBlink: faceData.eyeBlink,
      headMovement: {
        x: faceData.headPose.yaw,
        y: faceData.headPose.pitch,
        z: faceData.headPose.roll
      }
    }));
  };

  const startSpeechAnalysis = () => {
    if (!analyserRef.current) return;
    
    const analyzeSpeech = () => {
      if (avatarActive && analyserRef.current) {
        const bufferLength = analyserRef.current.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyserRef.current.getByteFrequencyData(dataArray);
        
        // Вычисляем интенсивность речи
        const average = dataArray.reduce((sum, value) => sum + value, 0) / bufferLength;
        const speechIntensity = Math.min(1, average / 100);
        
        // Определяем, говорит ли человек
        const isSpeaking = speechIntensity > avatarConfig.talkingSensitivity;
        
        setSpeechData({
          isSpeaking,
          intensity: speechIntensity,
          timestamp: Date.now()
        });
        
        // Обновляем статус аватара
        setAvatarStatus(prev => ({
          ...prev,
          isTalking: isSpeaking,
          speechIntensity: speechIntensity,
          mouthOpenness: isSpeaking ? speechIntensity * 0.8 : 0,
          emotion: isSpeaking ? 'happy' : 'neutral'
        }));
        
        requestAnimationFrame(analyzeSpeech);
      }
    };
    
    analyzeSpeech();
  };

  const stopSpeechAnalysis = () => {
    setSpeechData(null);
    setAvatarStatus(prev => ({
      ...prev,
      isTalking: false,
      speechIntensity: 0,
      mouthOpenness: 0
    }));
  };

  const startAudioAnalysis = () => {
    if (!audioContextRef.current || !analyserRef.current) return;
    
    try {
      // Получаем доступ к микрофону
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          const source = audioContextRef.current.createMediaStreamSource(stream);
          source.connect(analyserRef.current);
          console.log('Audio analysis started');
        })
        .catch(error => {
          console.error('Error accessing microphone:', error);
        });
    } catch (error) {
      console.error('Error starting audio analysis:', error);
    }
  };

  const stopAudioAnalysis = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  };

  const startAvatarStream = async () => {
    try {
      // Здесь должен быть вызов API для запуска avatar stream
      console.log('Starting avatar stream...');
      
      // Имитируем успешный запуск
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Avatar stream started');
      
    } catch (error) {
      console.error('Error starting avatar stream:', error);
      throw error;
    }
  };

  const stopAvatarStream = () => {
    console.log('Stopping avatar stream...');
    // Здесь должен быть вызов API для остановки avatar stream
  };

  const toggleAvatar = () => {
    setAvatarActive(prev => !prev);
  };

  const updateAvatarConfig = (newConfig) => {
    setAvatarConfig(prev => ({
      ...prev,
      ...newConfig
    }));
  };

  const handleAvatarClick = useCallback((participantId, status) => {
    console.log('Avatar clicked for participant:', participantId, status);
    
    // Можно добавить дополнительную логику при клике на аватар
    // Например, показать детальную информацию или настройки
  }, []);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Подключен';
      case 'connecting': return 'Подключение...';
      case 'error': return 'Ошибка';
      default: return 'Отключен';
    }
  };

  return (
    <div className={`avatar-meeting-integration ${className}`}>
      {/* Панель управления аватаром */}
      <Card className="avatar-control-panel">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold">AI Avatar</h3>
            <Badge className={`${getConnectionStatusColor()} text-white`}>
              {getConnectionStatusText()}
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              onClick={toggleAvatar}
              variant={avatarActive ? "destructive" : "default"}
              size="sm"
            >
              {avatarActive ? "Отключить" : "Включить"} аватар
            </Button>
          </div>
        </div>

        {/* Статус аватара */}
        {avatarActive && (
          <div className="px-4 pb-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Состояние:</span>
                <span className={`ml-2 ${avatarStatus.isTalking ? 'text-orange-500' : 'text-green-500'}`}>
                  {avatarStatus.isTalking ? 'Говорит' : 'Слушает'}
                </span>
              </div>
              <div>
                <span className="font-medium">Эмоция:</span>
                <span className="ml-2 capitalize">{avatarStatus.emotion}</span>
              </div>
              <div>
                <span className="font-medium">Интенсивность речи:</span>
                <span className="ml-2">{Math.round(avatarStatus.speechIntensity * 100)}%</span>
              </div>
              <div>
                <span className="font-medium">Открытие рта:</span>
                <span className="ml-2">{Math.round(avatarStatus.mouthOpenness * 100)}%</span>
              </div>
            </div>

            {/* Индикаторы */}
            <div className="mt-3 flex gap-2">
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${avatarStatus.eyeBlink ? 'bg-blue-500' : 'bg-gray-300'}`} />
                <span className="text-xs">Моргание</span>
              </div>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${faceTrackingData?.faceDetected ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-xs">Face Tracking</span>
              </div>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${speechData?.isSpeaking ? 'bg-orange-500' : 'bg-gray-300'}`} />
                <span className="text-xs">Речь</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Overlay аватара */}
      {avatarActive && (
        <AvatarOverlay
          participantId={participantId}
          isActive={avatarActive}
          avatarConfig={avatarConfig}
          onAvatarClick={handleAvatarClick}
          className="fixed inset-0 pointer-events-none"
        />
      )}

      <style jsx>{`
        .avatar-meeting-integration {
          position: relative;
        }
        
        .avatar-control-panel {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </div>
  );
};

export default AvatarMeetingIntegration;
