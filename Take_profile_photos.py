import json
import requests
from pprint import pprint
from urllib.parse import urlencode
import time
from tqdm import tqdm
import configparser
import os
from datetime import datetime

config = configparser.ConfigParser()
config.read("settings.ini")
name_fold = config["Yandex"]["name_fold"]
token_ya = config["Yandex"]["yan_oauth_token"]
owner_id = config["VK"]["owner_id"]
count = int(config["Yandex"]["count"])
token_vk = config["VK"]["token_vk"]

dict_head = {"Authorization": f"OAuth {token_ya}"}
base_url_yandex = "https://cloud-api.yandex.net"
url_yandex_folder = f"{base_url_yandex}/v1/disk/resources?path={name_fold}"
response = requests.put(url_yandex_folder, headers=dict_head)

class SAVEPHOTOClient:
    base_url_VK = "https://api.vk.com/method"
    base_url_yandex = "https://cloud-api.yandex.net"

    def __init__(self, token_vk, owner_id, token_ya, count):
        self.token_vk = token_vk
        self.owner_id = owner_id
        self.token_ya = token_ya
        self.count = count
        dict_head = {
            "Authorization": f"OAuth {self.token_ya}"
        }

    def upload_photo_profile(self):
        params = {
            "access_token":  self.token_vk,
            "owner_id": self.owner_id,
            "album_id": "profile",
            "extended": 1,
            "photo_sizes": 1,
            "v": 5.131
        }
        response = requests.get(f"{self.base_url_VK}/photos.get", params=params)
        return response.json()

    def take_photos(self):
        names_list = []
        info_about_photos = []
        list_of_photos = self.upload_photo_profile().get("response").get("items")
        for items in list_of_photos:
            max_height = 0
            max_width = 0
            first_name = items.get("likes", {}).get("count")
            second_name = f".date-{datetime.fromtimestamp(items.get("date")).date()}"
            third_name = f".id-{items.get("id")}"
            for max_photo_resol in items.get('sizes'):
                if max_photo_resol.get("height") > max_height or max_photo_resol.get("width") > max_width:
                    max_height = max_photo_resol.get("height")
                    max_width = max_photo_resol.get("width")
                    url_photo = max_photo_resol.get("url")
            name = f"{first_name}.jpg"
            if name in names_list:
                name = f"{first_name}{second_name}.jpg"
                if name in names_list:
                    name = f"{first_name}{second_name}{third_name}.jpg"
            names_list.append(name)
            photo = {"file_name": name, "size": [max_height, max_width], "url": url_photo, "number": first_name}
            info_about_photos.append(photo)
        return info_about_photos

    def count_sorted(self):
        photo_rating = []
        list_photo = self.take_photos()
        qty_photos = len(list_photo)
        if qty_photos < self.count:
            self.count = qty_photos
        for photo in list_photo:
            photo_rating.append(photo.get("number"))
        photo_rating.sort()
        photo_rating = photo_rating[:-self.count-1:-1]
        return [serch_photo for serch_photo in list_photo if serch_photo.get("number") in photo_rating]

    def load_photos(self):
        answer = []
        found_photos = self.count_sorted()
        for items in tqdm(found_photos):
            response = requests.get(items.get("url"))
            name = items.get("file_name")
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

            response = requests.get(f"{base_url_yandex}/v1/disk/resources?public_key={name_fold}",
                                    params=params_image, headers=dict_head)
            name_file = response.json().get('name')
            size_file = response.json().get('size')
            list_photos = {"file_name": name_file, "size": size_file}
            answer.append(list_photos)
        pprint(answer)

if __name__ == "__main__":
    vk_client = SAVEPHOTOClient(token_vk, owner_id, token_ya, count)
    storage_photo = vk_client.load_photos()