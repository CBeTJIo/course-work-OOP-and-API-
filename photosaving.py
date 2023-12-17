import json
import requests
from pprint import pprint
from urllib.parse import urlencode
import time
from tqdm import tqdm
import configparser

config = configparser.ConfigParser()
config.read("settings.ini")

name_fold = config["Yandex"]["name_fold"]
Yan_OAuth_token = config["Yandex"]["Yan_OAuth_token"]
owner_id = config["VK"]["owner_id"]
count = int(config["Yandex"]["count"])
dict_head = {
    "Authorization": f"OAuth {Yan_OAuth_token}"
}

base_url_yandex = "https://cloud-api.yandex.net"
url_yandex_folder = f"{base_url_yandex}/v1/disk/resources?path={name_fold}"
response = requests.put(url_yandex_folder, headers=dict_head)

# Мой куратор - Филипп Воронов (Discord — fivoronov)

TOKEN = config["VK"]["TOKEN"]

class SAVEPHOTOClient:
    base_url = "https://api.vk.com/method"

    def __init__(self, token, owner_id):
        self.token = token
        self.owner_id = owner_id

    def get_photo(self):
        params = {
            "access_token":  self.token,
            "owner_id": self.owner_id,
            "album_id": "profile",
            "extended": 1,
            "photo_sizes": 1,
            "v": 5.131
        }
        response = requests.get(f"{self.base_url}/photos.get", params=params)
        return response.json()

if __name__ == "__main__":
    vk_client = SAVEPHOTOClient(TOKEN, owner_id)
    storage_photo = vk_client.get_photo()

names_list = []
info_about_photo = []
name_sorted = []

for items in storage_photo.get("response").get("items"):
    max_height = 0
    max_width = 0
    url_photo = ""
    first_name = items.get("likes", {}).get("count")
    second_name = items.get("date")
    for max_photo_resol in items.get('sizes'):
        if max_photo_resol.get("height") > max_height or max_photo_resol.get("width")> max_width:
            max_height = max_photo_resol.get("height")
            max_width = max_photo_resol.get("width")
            url_photo = max_photo_resol.get("url")
    name = f"{first_name}.jpg"
    if name in names_list:
        name = f"{first_name}{second_name}.jpg"
    names_list.append(name)
    name_sorted.append(first_name)
    list_photos = {"file_name": name, "size": [max_height, max_width], "url": url_photo, "number": first_name, "number_second": second_name}
    info_about_photo.append(list_photos)

name_sorted.sort()
list_count = []

# выгрузка фото по необходимому количеству (count)
if len(info_about_photo) < count:
    count = len(info_about_photo)
x = 1
while x < (count + 1):
    list_count.append(name_sorted[-x])
    x += 1
found_photos = []
for serch_photo in info_about_photo:
    check_foto = 1
    double = 0
    while len(info_about_photo) > check_foto-1:
        if serch_photo.get("number") == name_sorted[-check_foto] and name_sorted[-check_foto] in list_count:
            if double > 0:
                break
            else:
                found_photos.append(serch_photo)
                double += 1
        check_foto += 1

# загрузка фото на яндекс
answer = []
list_of_names = []
for items in tqdm(found_photos):
    response = requests.get(items.get("url"))
    if items.get("file_name") in list_of_names:
        name = f"{items.get("number_second")}.jpg"
    else:
        name = items.get("file_name")
    list_of_names.append(name)

    list_photos = {"file_name": name, "size": [max_height, max_width]}
    answer.append(list_photos)

    with open(name, "wb") as f:
        f.write(response.content)

    url_yandex_request = f"{base_url_yandex}/v1/disk/resources/upload"
    params_image = {
        "path": f"{name_fold}/{name}"
    }
    response = requests.get(url_yandex_request, params=params_image, headers=dict_head)

    url_for_upload = response.json().get('href')

    with open(name, "rb") as f:
        response = requests.put(url_for_upload, files={'file': f})

pprint(answer)