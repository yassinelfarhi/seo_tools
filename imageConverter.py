import base64
import json
import logging
import os
import subprocess
from io import BytesIO
from time import sleep
from uuid import uuid4

import requests
from PIL import Image

from MagentoMetas import MagentoMetas

logger = logging.getLogger(__name__)


class ImageConverter(MagentoMetas):

    def __init__(self, site_id, language) -> None:
        super().__init__(site_id, language)
        logging.basicConfig(filename='seo_app.log', level=logging.INFO)
        self.skus = []

    def get_products_skus(self):
        for i in range(1310):
            page = i + 1
            products_chunk = self.get_products_chunk(page, self.page_size)
            for product in products_chunk:
                print(product["sku"] + "\n")
                self.skus.append(product["sku"])

        with open('data/skus.json', 'w') as json_file:
            json.dump(self.skus, json_file)

    def convert(self):
        for i in range(1300, 1310):
            page = i + 1
            self.token = self.get_token()
            product_list = self.get_products_chunk(page, self.page_size)
            for product in product_list:
                sleep(1)
                index = 1
                media_url = f'https://eexera.com/rest/default/V1/products/{product["sku"]}/media'
                header = {'Authorization': f'Bearer {self.token}'}
                medias = requests.get(media_url, headers=header)
                items = json.loads(medias.text)
                for item in items:
                    # Saving retrieved image
                    sleep(1)
                    url = f'https://eexera.com/pub/media/catalog/product{item["file"]}'
                    print(url)
                    response = requests.get(url)
                    rand_token = uuid4()
                    extension = item['file'].split('.')[-1]
                    old_image_name = str(rand_token) + "." + extension
                    old_image_path = "data/" + old_image_name

                    with open(old_image_path, "wb") as old_image:
                        old_image.write(response.content)

                    # Converting retrieved image
                    image = Image.open(old_image_path)
                    rand_token = uuid4()
                    image_name = str(rand_token) + ".jpg"
                    image_save_path = "data/" + image_name

                    image.save(image_save_path, 'jpeg', optimize=True, quality=40)

                    old_size = os.path.getsize(old_image_path)
                    new_size = os.path.getsize(image_save_path)
                    ratio = new_size / old_size
                    gained_size = (1 - ratio) * 100

                    if ratio < 1:
                        with open(image_save_path, "rb") as jpeg_image:
                            jpeg_64_encoded = base64.b64encode(jpeg_image.read()).decode('utf-8')

                        file_path = item['file'].split("/")
                        file_path.pop()
                        file_path = "/".join(file_path)
                        file_path = f'{file_path}/{image_name}'

                        data = {
                            "entry": {
                                "id": item["id"],
                                "media_type": item["media_type"],
                                "label": "",
                                "position": item["position"],
                                "disabled": item["disabled"],
                                "types": item["types"],
                                "file": file_path,
                                "content": {
                                    "base64_encoded_data": jpeg_64_encoded,
                                    "type": "image/jpeg",
                                    "name": image_name
                                }
                            }
                        }

                        media_post_url = f'https://eexera.com/rest/default/V1/products/{product["sku"]}/media/{item["id"]}'
                        response = requests.put(media_post_url, json=data, headers=header)

                        logger.info(
                            f'{item["file"]} optimized | original size : {old_size} | modified size : {new_size} |  '
                            f'gained size : {gained_size} % | page : {page} | product : {product["sku"]} |ratio: '
                            f'{ratio}')

                        os.remove(image_save_path)
                        os.remove(old_image_path)


converter = ImageConverter('default', 'italien')
converter.convert()
