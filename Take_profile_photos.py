import json
import requests
from pprint import pprint
from urllib.parse import urlencode
import time
from tqdm import tqdm
import configparser
import os
from datetime import datetime

class SavePhotoClient:
    base_url_VK = "https://api.vk.com/method"
    base_url_yandex = "https://cloud-api.yandex.net"
    config = configparser.ConfigParser()
    config.read("settings.ini")
    owner_id = config["VK"]["owner_id"]
    token_vk = config["VK"]["token_vk"]
    token_ya = config["Yandex"]["yan_oauth_token"]
    name_fold = config["Yandex"]["name_fold"]
    dict_head = {
        "Authorization": f"OAuth {token_ya}"
    }

    def create_folder(self):
        url_yandex_folder = f"{self.base_url_yandex}/v1/disk/resources?path={self.name_fold}"
        response = requests.put(url_yandex_folder, headers=self.dict_head)
        return self.name_fold

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
        count = int(self.config["Yandex"]["count"])
        list_photo = self.take_photos()
        qty_photos = len(list_photo)
        if qty_photos < count:
            count = qty_photos
        for photo in list_photo:
            photo_rating.append(photo.get("number"))
        photo_rating.sort()
        photo_rating = photo_rating[-count:]
        check_count = 1
        sorted_list_photo = []
        while count > check_count - 1:
            double = 0
            for serch_photo in list_photo:
                if serch_photo.get("number") == photo_rating[-check_count]:
                    if double > 0:
                        continue
                    else:
                        sorted_list_photo.append(serch_photo)
                        double += 1
            check_count += 1
        return sorted_list_photo

    def load_photos(self):
        answer = []
        found_photos = self.count_sorted()
        name_fold = self.create_folder()
        for items in tqdm(found_photos):
            response = requests.get(items.get("url"))
            name = items.get("file_name")
            with open(name, "wb") as f:
                f.write(response.content)
            url_yandex_request = f"{self.base_url_yandex}/v1/disk/resources/upload"
            params_image = {
                "path": f"{name_fold}/{name}"
            }
            response = requests.get(url_yandex_request, params=params_image, headers=self.dict_head)
            url_for_upload = response.json().get('href')
            with open(name, "rb") as f:
                response = requests.put(url_for_upload, files={'file': f})

            response = requests.get(f"{self.base_url_yandex}/v1/disk/resources?public_key={name_fold}",
                                    params=params_image, headers=self.dict_head)
            name_file = response.json().get('name')
            size_file = response.json().get('size')
            list_photos = {"file_name": name_file, "size": size_file}
            answer.append(list_photos)
        pprint(answer)

if __name__ == "__main__":
    SavePhotoClient().load_photos()