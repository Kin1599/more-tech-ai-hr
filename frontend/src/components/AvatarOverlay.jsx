/**
 * AvatarOverlay - Компонент для отображения AI аватара поверх видео участника.
 * 
 * Проецирует видеопоток AI аватара на фронтенд с возможностью настройки
 * позиционирования и прозрачности.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card } from './ui/card';

const AvatarOverlay = ({ 
  participantId, 
  isActive = false, 
  avatarConfig = {},
  onAvatarClick = () => {},
  className = ""
}) => {
  const [avatarStream, setAvatarStream] = useState(null);
  const [avatarStatus, setAvatarStatus] = useState({
    isTalking: false,
    emotion: 'neutral',
    mouthOpenness: 0,
    eyeBlink: false,
    headMovement: { x: 0, y: 0, z: 0 }
  });
  const [overlaySettings, setOverlaySettings] = useState({
    opacity: 0.9,
    position: 'center', // center, top-left, top-right, bottom-left, bottom-right
    scale: 1.0,
    showStatus: true,
    showControls: false
  });

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);

  // Конфигурация по умолчанию
  const defaultConfig = {
    resolution: [640, 480],
    fps: 30,
    faceId: 'default_face',
    talkingSensitivity: 0.3,
    emotionDetection: true,
    headMovementEnabled: true,
    eyeBlinkEnabled: true,
    backgroundColor: [50, 50, 50],
    avatarScale: 0.8,
    ...avatarConfig
  };

  useEffect(() => {
    if (isActive) {
      initializeAvatarStream();
    } else {
      cleanupAvatarStream();
    }

    return () => {
      cleanupAvatarStream();
    };
  }, [isActive, participantId]);

  useEffect(() => {
    if (avatarStream && videoRef.current) {
      setupVideoElement();
    }
  }, [avatarStream]);

  useEffect(() => {
    if (isActive) {
      startAnimationLoop();
    } else {
      stopAnimationLoop();
    }

    return () => {
      stopAnimationLoop();
    };
  }, [isActive]);

  const initializeAvatarStream = async () => {
    try {
      // Получаем видеопоток аватара через VideoSDK
      const stream = await getAvatarVideoStream(participantId);
      if (stream) {
        setAvatarStream(stream);
        console.log('Avatar stream initialized for participant:', participantId);
      }
    } catch (error) {
      console.error('Error initializing avatar stream:', error);
    }
  };

  const getAvatarVideoStream = async (participantId) => {
    try {
      // Здесь должен быть вызов VideoSDK API для получения avatar stream
      // Пока используем заглушку
      return createMockAvatarStream();
    } catch (error) {
      console.error('Error getting avatar stream:', error);
      return null;
    }
  };

  const createMockAvatarStream = () => {
    // Создаем mock stream для демонстрации
    const canvas = document.createElement('canvas');
    canvas.width = defaultConfig.resolution[0];
    canvas.height = defaultConfig.resolution[1];
    
    const ctx = canvas.getContext('2d');
    const stream = canvas.captureStream(defaultConfig.fps);
    
    // Запускаем анимацию на canvas
    animateMockAvatar(ctx, canvas.width, canvas.height);
    
    return stream;
  };

  const animateMockAvatar = (ctx, width, height) => {
    const animate = () => {
      // Очищаем canvas
      ctx.fillStyle = `rgb(${defaultConfig.backgroundColor.join(',')})`;
      ctx.fillRect(0, 0, width, height);

      // Рисуем простой аватар
      drawMockAvatar(ctx, width, height);

      requestAnimationFrame(animate);
    };
    animate();
  };

  const drawMockAvatar = (ctx, width, height) => {
    const centerX = width / 2;
    const centerY = height / 2;
    const avatarSize = Math.min(width, height) * defaultConfig.avatarScale;

    // Голова
    const headRadius = avatarSize * 0.3;
    ctx.fillStyle = '#C8B4A0'; // телесный цвет
    ctx.beginPath();
    ctx.arc(centerX, centerY, headRadius, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#A09080';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Глаза
    const eyeY = centerY - headRadius * 0.3;
    const eyeSize = headRadius * 0.15;

    // Левый глаз
    const leftEyeX = centerX - headRadius * 0.3;
    if (avatarStatus.eyeBlink) {
      // Закрытый глаз
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(leftEyeX - eyeSize, eyeY);
      ctx.lineTo(leftEyeX + eyeSize, eyeY);
      ctx.stroke();
    } else {
      // Открытый глаз
      ctx.fillStyle = '#FFF';
      ctx.beginPath();
      ctx.arc(leftEyeX, eyeY, eyeSize, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Зрачок
      ctx.fillStyle = '#000';
      ctx.beginPath();
      ctx.arc(leftEyeX, eyeY, eyeSize / 2, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Правый глаз
    const rightEyeX = centerX + headRadius * 0.3;
    if (avatarStatus.eyeBlink) {
      // Закрытый глаз
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(rightEyeX - eyeSize, eyeY);
      ctx.lineTo(rightEyeX + eyeSize, eyeY);
      ctx.stroke();
    } else {
      // Открытый глаз
      ctx.fillStyle = '#FFF';
      ctx.beginPath();
      ctx.arc(rightEyeX, eyeY, eyeSize, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();

      // Зрачок
      ctx.fillStyle = '#000';
      ctx.beginPath();
      ctx.arc(rightEyeX, eyeY, eyeSize / 2, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Рот
    const mouthY = centerY + headRadius * 0.4;
    const mouthWidth = headRadius * 0.4;

    if (avatarStatus.isTalking) {
      // Открытый рот
      const mouthHeight = avatarStatus.mouthOpenness * headRadius * 0.3;
      ctx.fillStyle = '#8B4513';
      ctx.beginPath();
      ctx.ellipse(centerX, mouthY, mouthWidth / 2, mouthHeight / 2, 0, 0, 2 * Math.PI);
      ctx.fill();
    } else {
      // Закрытый рот
      ctx.strokeStyle = '#8B4513';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(centerX, mouthY, mouthWidth / 2, 0, Math.PI);
      ctx.stroke();
    }

    // Индикатор состояния
    if (overlaySettings.showStatus) {
      ctx.fillStyle = '#FFF';
      ctx.font = '16px Arial';
      ctx.textAlign = 'left';
      ctx.fillText(`AI Avatar - ${avatarStatus.emotion}`, 10, height - 30);
      
      if (avatarStatus.isTalking) {
        ctx.fillText('Speaking', 10, height - 10);
      }
    }
  };

  const setupVideoElement = () => {
    if (videoRef.current && avatarStream) {
      videoRef.current.srcObject = avatarStream;
      videoRef.current.play().catch(console.error);
    }
  };

  const cleanupAvatarStream = () => {
    if (avatarStream) {
      avatarStream.getTracks().forEach(track => track.stop());
      setAvatarStream(null);
    }
  };

  const startAnimationLoop = () => {
    const animate = () => {
      // Обновляем статус аватара (имитация данных с бэкенда)
      updateAvatarStatus();
      
      animationRef.current = requestAnimationFrame(animate);
    };
    animate();
  };

  const stopAnimationLoop = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
  };

  const updateAvatarStatus = () => {
    // Имитация обновления статуса аватара
    const now = Date.now();
    
    // Случайное моргание
    if (Math.random() < 0.01) { // 1% шанс моргнуть каждый кадр
      setAvatarStatus(prev => ({ ...prev, eyeBlink: true }));
      setTimeout(() => {
        setAvatarStatus(prev => ({ ...prev, eyeBlink: false }));
      }, 150);
    }

    // Имитация речи
    const isTalking = Math.sin(now / 1000) > 0.5;
    const mouthOpenness = isTalking ? Math.random() * 0.8 : 0;
    
    setAvatarStatus(prev => ({
      ...prev,
      isTalking,
      mouthOpenness,
      emotion: isTalking ? 'happy' : 'neutral'
    }));
  };

  const handleAvatarClick = () => {
    onAvatarClick(participantId, avatarStatus);
  };

  const toggleControls = () => {
    setOverlaySettings(prev => ({
      ...prev,
      showControls: !prev.showControls
    }));
  };

  const updateOverlaySetting = (key, value) => {
    setOverlaySettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (!isActive) {
    return null;
  }

  const getPositionStyles = () => {
    const positions = {
      'center': { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' },
      'top-left': { top: '10px', left: '10px' },
      'top-right': { top: '10px', right: '10px' },
      'bottom-left': { bottom: '10px', left: '10px' },
      'bottom-right': { bottom: '10px', right: '10px' }
    };
    
    return positions[overlaySettings.position] || positions.center;
  };

  return (
    <div 
      className={`avatar-overlay ${className}`}
      style={{
        position: 'absolute',
        zIndex: 1000,
        opacity: overlaySettings.opacity,
        transform: `scale(${overlaySettings.scale})`,
        ...getPositionStyles()
      }}
    >
      <Card className="avatar-container">
        <div className="relative">
          {/* Видео элемент аватара */}
          <video
            ref={videoRef}
            className="avatar-video"
            style={{
              width: defaultConfig.resolution[0],
              height: defaultConfig.resolution[1],
              borderRadius: '8px',
              objectFit: 'cover'
            }}
            muted
            playsInline
            onClick={handleAvatarClick}
          />
          
          {/* Canvas для fallback анимации */}
          <canvas
            ref={canvasRef}
            className="avatar-canvas"
            style={{
              width: defaultConfig.resolution[0],
              height: defaultConfig.resolution[1],
              borderRadius: '8px',
              display: avatarStream ? 'none' : 'block'
            }}
          />

          {/* Индикатор состояния */}
          {overlaySettings.showStatus && (
            <div className="avatar-status-indicator">
              <div className={`status-dot ${avatarStatus.isTalking ? 'talking' : 'idle'}`} />
              <span className="status-text">
                {avatarStatus.isTalking ? 'Speaking' : 'Listening'}
              </span>
            </div>
          )}

          {/* Кнопка настроек */}
          <button
            className="avatar-settings-btn"
            onClick={toggleControls}
            title="Настройки аватара"
          >
            ⚙️
          </button>

          {/* Панель настроек */}
          {overlaySettings.showControls && (
            <div className="avatar-controls-panel">
              <div className="control-group">
                <label>Прозрачность:</label>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={overlaySettings.opacity}
                  onChange={(e) => updateOverlaySetting('opacity', parseFloat(e.target.value))}
                />
              </div>
              
              <div className="control-group">
                <label>Масштаб:</label>
                <input
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={overlaySettings.scale}
                  onChange={(e) => updateOverlaySetting('scale', parseFloat(e.target.value))}
                />
              </div>
              
              <div className="control-group">
                <label>Позиция:</label>
                <select
                  value={overlaySettings.position}
                  onChange={(e) => updateOverlaySetting('position', e.target.value)}
                >
                  <option value="center">Центр</option>
                  <option value="top-left">Верх-лево</option>
                  <option value="top-right">Верх-право</option>
                  <option value="bottom-left">Низ-лево</option>
                  <option value="bottom-right">Низ-право</option>
                </select>
              </div>
              
              <div className="control-group">
                <label>
                  <input
                    type="checkbox"
                    checked={overlaySettings.showStatus}
                    onChange={(e) => updateOverlaySetting('showStatus', e.target.checked)}
                  />
                  Показывать статус
                </label>
              </div>
            </div>
          )}
        </div>
      </Card>

      <style jsx>{`
        .avatar-overlay {
          transition: all 0.3s ease;
        }
        
        .avatar-container {
          background: rgba(0, 0, 0, 0.1);
          border: 2px solid rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(10px);
        }
        
        .avatar-video, .avatar-canvas {
          cursor: pointer;
          transition: transform 0.2s ease;
        }
        
        .avatar-video:hover, .avatar-canvas:hover {
          transform: scale(1.05);
        }
        
        .avatar-status-indicator {
          position: absolute;
          top: 8px;
          left: 8px;
          display: flex;
          align-items: center;
          gap: 6px;
          background: rgba(0, 0, 0, 0.7);
          padding: 4px 8px;
          border-radius: 12px;
          color: white;
          font-size: 12px;
        }
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #4ade80;
          animation: pulse 2s infinite;
        }
        
        .status-dot.talking {
          background: #f59e0b;
          animation: pulse 0.5s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        .avatar-settings-btn {
          position: absolute;
          top: 8px;
          right: 8px;
          background: rgba(0, 0, 0, 0.7);
          border: none;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
        }
        
        .avatar-settings-btn:hover {
          background: rgba(0, 0, 0, 0.9);
        }
        
        .avatar-controls-panel {
          position: absolute;
          top: 40px;
          right: 8px;
          background: rgba(0, 0, 0, 0.9);
          color: white;
          padding: 12px;
          border-radius: 8px;
          min-width: 200px;
          font-size: 12px;
        }
        
        .control-group {
          margin-bottom: 8px;
        }
        
        .control-group label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        
        .control-group input[type="range"] {
          width: 100%;
        }
        
        .control-group select {
          width: 100%;
          padding: 2px 4px;
          border-radius: 4px;
          background: white;
          color: black;
        }
        
        .control-group input[type="checkbox"] {
          margin-right: 6px;
        }
      `}</style>
    </div>
  );
};

export default AvatarOverlay;
