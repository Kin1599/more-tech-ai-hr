import React, {useState, useEffect} from 'react';
import {Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter} from './ui/dialog';
import {Button} from './ui/button';
import {Input} from './ui/input';
import {Label} from './ui/label';
import {getUserProfile} from '../Api';
import {useStore} from '../App/store';

const ProfileEditModal = ({isOpen, onClose}) => {
  const {updateUserProfile: updateProfile, successToast, errorToast} = useStore();
  const [profile, setProfile] = useState({
    name: '',
    surname: '',
    patronymic: '',
    contacts: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Загружаем профиль при открытии модального окна
  useEffect(() => {
    if (isOpen) {
      loadProfile();
    }
  }, [isOpen]);

  const loadProfile = async () => {
    setIsLoading(true);
    try {
      const data = await getUserProfile();
      setProfile({
        name: data.name || '',
        surname: data.surname || '',
        patronymic: data.patronymic || '',
        contacts: data.contacts || '',
      });
    } catch (error) {
      console.error('Ошибка при загрузке профиля:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const result = await updateProfile(profile);
      if (result.success) {
        successToast('Профиль обновлен', 'Ваши данные успешно сохранены');
        onClose();
      } else {
        errorToast('Ошибка', result.error || 'Не удалось сохранить профиль');
      }
    } catch (error) {
      console.error('Ошибка при сохранении профиля:', error);
      errorToast('Ошибка', 'Не удалось сохранить профиль');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className='sm:max-w-md'>
        <DialogHeader>
          <DialogTitle className='text-xl font-semibold'>Редактирование профиля</DialogTitle>
        </DialogHeader>

        <div className='space-y-4 py-4'>
          {isLoading ? (
            <div className='flex justify-center py-8'>
              <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-[#eb5e28]'></div>
            </div>
          ) : (
            <>
              <div className='space-y-2'>
                <Label htmlFor='name'>Имя</Label>
                <Input
                  id='name'
                  value={profile.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder='Введите имя'
                />
              </div>

              <div className='space-y-2'>
                <Label htmlFor='surname'>Фамилия</Label>
                <Input
                  id='surname'
                  value={profile.surname}
                  onChange={(e) => handleInputChange('surname', e.target.value)}
                  placeholder='Введите фамилию'
                />
              </div>

              <div className='space-y-2'>
                <Label htmlFor='patronymic'>Отчество</Label>
                <Input
                  id='patronymic'
                  value={profile.patronymic}
                  onChange={(e) => handleInputChange('patronymic', e.target.value)}
                  placeholder='Введите отчество'
                />
              </div>

              <div className='space-y-2'>
                <Label htmlFor='contacts'>Контакты</Label>
                <Input
                  id='contacts'
                  value={profile.contacts}
                  onChange={(e) => handleInputChange('contacts', e.target.value)}
                  placeholder='Введите контакты'
                />
              </div>
            </>
          )}
        </div>

        <DialogFooter className='flex gap-3'>
          <Button variant='outline' onClick={onClose} disabled={isSaving} className='cursor-pointer'>
            Отмена
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving || isLoading}
            className='bg-[#eb5e28] hover:bg-[#d54e1a] text-white cursor-pointer'
          >
            {isSaving ? (
              <>
                <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2'></div>
                Сохранение...
              </>
            ) : (
              'Сохранить'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ProfileEditModal;
