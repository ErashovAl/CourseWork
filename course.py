import time
import shutil
import requests
import os
import json
from pathlib import Path
import urllib.request
from progress.bar import Bar

class VkLoader:
    def __init__(self, token):
        self.token = token
            
    def foto_loader(self, vk_id, num_photo):
        
        URL = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id' : vk_id,
            'album_id' : 'profile',
            'access_token' : self.token,
            'v' : '5.131',
            'extended' : '1',
            'photos_sizes' : '1'
            }
        response = requests.get(URL, params=params).json()
        if 'error' in response.keys():
            return 'неверные данные VK'
         
        resp = response['response']['items']
        album_count = response['response']['count']
        if album_count == 0:
            return 'в этом альбоме нет фото'
        path = Path('photo')
        info = []
        count_img = 0
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)

        with open('data.json', 'w', encoding='utf-8') as f:
            
            if album_count < num_photo:
                print(f'Будет загружено меньше фото, т.к. в выбранном альбоме их только {album_count}!')
                album_count = num_photo
            for file in resp:
                if count_img == num_photo:
                    break
                like = dict(file['likes'])
                like = like['count']
                date = file['date']
                name = f'{like}_{date}'
                photo_link = file['sizes'][-1]
                photo_link_url = photo_link['url']
                count_img += 1
                
                img = urllib.request.urlopen(photo_link_url).read()
                with open('photo/' + name + '.jpg', "wb") as photo_in:
                    photo_in.write(img)
                    photo_info = {'file_name' : name, 'size' : photo_link['type']}
                    info.append(json.dumps(photo_info))
                
            json.dump(info, f)
        return

class YaUploader:
    def __init__(self, token):
        self.token = token

    def new_folder(self, folder_name):
        new_folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = {'Content-Type': 'application/json', 'Authorization': self.token}
        params = {'path': folder_name}
        resp = requests.put(new_folder_url, headers=headers, params=params)
        
        if resp.status_code == 201:
            print('New folder success')
        elif resp.status_code == 409:
            print('Папка уже существует')
        elif resp.status_code == 401:
            return 'Ошибка авторизации'
        else: return 'Что-то пошло не так'
        return

    def upload(self, ya_folder_name, count_photo):        
        
        path_to_photo = 'photo'
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload/'
        headers = {'Content-Type': 'application/json',
                    'Authorization': self.token}

        with Bar('Uploading', max=count_photo) as bar:
            for file in Path(path_to_photo).iterdir():
                name = os.path.basename(file)
                href = requests.get(upload_url, headers=headers, params={'path': ya_folder_name + '/' + name, 'overwrite': 'true'})
                requests.put(href.json().get('href', ''), data=open(path_to_photo + '/' + name, 'rb'))
                bar.next()

        print('\ncopying fotos from VK to YaD successfully')
        time.sleep(5)
        return
        
if __name__ == '__main__':

    def main():
        print('Загрузчик Фото из ВК на Я_Диск: ')
        token_VK = input('введите токен ВКонтакте: ')
        
        vk_id = input('введите ID Вконтакте: ')
        if not vk_id:
            print('не корректный ID')
            return
        count_photo = input('сколько фото следует загрузить: ')
        if not count_photo or count_photo == '0':
            print('неправильное количество фото')
            return
        count_photo = int(count_photo)
        pict_from_VK = VkLoader(token_VK)
        error = pict_from_VK.foto_loader(vk_id, count_photo)
        if error is not None:
            print("Не удалось загрузить фото с ВК: " + error)
            return
        tokenYD = input('введите токен ЯндексДиска: ')
        uploader = YaUploader(tokenYD)
        ya_folder_name = input('введите название новой папки ЯднексДиска для загрузки фото: ')
        error = uploader.new_folder(ya_folder_name)
        if error is not None:
            print("Не удалось создать папку на ЯндексДиске: " + error)
            return
        uploader.upload(ya_folder_name, count_photo)
        remove_folder = Path('photo')
        shutil.rmtree (remove_folder)
        time.sleep(2)

main()