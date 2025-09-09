import React from 'react';
import {MeetingProvider, useMeeting} from '@videosdk.live/react-sdk';
import {useParams, useNavigate} from 'react-router-dom';
import {Button} from '../../components/ui/button';

function MeetingView() {
  const {join, leave, participants, toggleMic, toggleWebcam, micOn, webcamOn} = useMeeting();
  const navigate = useNavigate();
  const [isJoined, setIsJoined] = React.useState(false);

  // Отладка состояния микрофона и камеры
  React.useEffect(() => {
    console.log('MeetingView: micOn changed to:', micOn);
    console.log('MeetingView: webcamOn changed to:', webcamOn);
  }, [micOn, webcamOn]);

  const handleJoin = () => {
    console.log('Joining meeting...');
    join();
    setIsJoined(true);
  };

  const handleLeave = () => {
    console.log('Leaving meeting...');
    leave();
    setIsJoined(false);
    navigate(-1); // Go back to the previous page
  };

  const handleToggleMic = () => {
    console.log('Toggle mic clicked. Current micOn:', micOn);
    toggleMic();
  };

  const handleToggleWebcam = () => {
    console.log('Toggle webcam clicked. Current webcamOn:', webcamOn);
    toggleWebcam();
  };

  return (
    <div className='min-h-screen bg-gray-100 p-4'>
      <div className='max-w-6xl mx-auto'>
        <div className='bg-white rounded-lg shadow-lg p-6'>
          <div className='flex justify-between items-center mb-6'>
            <h1 className='text-2xl font-bold text-gray-800'>Видеособеседование</h1>
            <div className='flex gap-3'>
              <Button
                onClick={handleJoin}
                disabled={isJoined}
                className={`${isJoined ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'} text-white`}
              >
                {isJoined ? 'Подключено' : 'Подключиться'}
              </Button>
              <Button onClick={handleLeave} variant='outline' className='border-red-500 text-red-500 hover:bg-red-50'>
                Покинуть
              </Button>
              <Button onClick={() => navigate(-1)} variant='outline'>
                Назад
              </Button>
            </div>
          </div>

          <div className='mb-6'>
            <h2 className='text-lg font-semibold mb-3'>Участники ({participants.size})</h2>
            <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
              {[...participants.keys()].map((id) => (
                <div key={id} className='bg-gray-50 p-4 rounded-lg border'>
                  <div className='flex items-center space-x-3'>
                    <div className='w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold'>
                      {id.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className='font-medium text-gray-800'>Участник {id}</p>
                      <p className='text-sm text-gray-500'>ID: {id}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className='flex justify-center gap-4 mb-6'>
            <Button
              onClick={handleToggleMic}
              disabled={!isJoined}
              className={`${!isJoined ? 'bg-gray-400 cursor-not-allowed' : micOn ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white`}
            >
              {micOn ? 'Микрофон Вкл' : 'Микрофон Выкл'}
            </Button>
            <Button
              onClick={handleToggleWebcam}
              disabled={!isJoined}
              className={`${!isJoined ? 'bg-gray-400 cursor-not-allowed' : webcamOn ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white`}
            >
              {webcamOn ? 'Камера Вкл' : 'Камера Выкл'}
            </Button>
          </div>

          <div className='text-center text-gray-500'>
            <p>
              {isJoined
                ? 'Собеседование активно. Управляйте микрофоном и камерой кнопками выше.'
                : 'Нажмите "Подключиться" чтобы начать собеседование'}
            </p>
            {isJoined && (
              <div className='mt-4 text-sm text-gray-400'>
                <p>
                  Отладка: Микрофон = {micOn ? 'ВКЛ' : 'ВЫКЛ'}, Камера = {webcamOn ? 'ВКЛ' : 'ВЫКЛ'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VideoInterviewPage() {
  const {roomId, token} = useParams();
  const navigate = useNavigate();

  if (!roomId || !token) {
    return (
      <div className='min-h-screen bg-gray-100 flex items-center justify-center'>
        <div className='bg-white rounded-lg shadow-lg p-8 text-center'>
          <h1 className='text-2xl font-bold text-red-600 mb-4'>Ошибка</h1>
          <p className='text-gray-600 mb-6'>Не удалось получить данные для видеособеседования</p>
          <Button onClick={() => navigate(-1)}>Вернуться назад</Button>
        </div>
      </div>
    );
  }

  return (
    <MeetingProvider
      config={{
        meetingId: roomId,
        micEnabled: true,
        webcamEnabled: true,
        name: 'Candidate',
      }}
      token={token}
      joinOnMount={false}
    >
      <MeetingView />
    </MeetingProvider>
  );
}
