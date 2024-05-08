import base64
import json
from io import BytesIO
from uuid import uuid4

import requests
from PIL import Image

from MagentoMetas import MagentoMetas


class ImageConverter(MagentoMetas):

    def __init__(self, site_id, language) -> None:
        super().__init__(site_id, language)
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
        for i in range(2):
            page = i + 1
            self.token = self.get_token()
            product_list = self.get_products_chunk(page, self.page_size)
            index = 1
            for product in product_list:
                media_url = f'https://eexera.com/rest/default/V1/products/{product["sku"]}/media'
                header = {'Authorization': f'Bearer {self.token}'}
                medias = requests.get(media_url, headers=header)
                items = json.loads(medias.text)
                for item in items:
                    url = f'https://eexera.com/pub/media/catalog/product{item["file"]}'
                    print(url)
                    response = requests.get(url)
                    image = Image.open(BytesIO(response.content))
                    image = image.convert('RGB')
                    rand_token = uuid4()
                    image_name = str(rand_token) + ".jpg"
                    image_save_path = "data/" + image_name
                    image.save(image_save_path, 'jpeg', optimize=True, quality=50)

                    with open(image_save_path, "rb") as jpeg_image:
                        jpeg_64_encoded = base64.b64encode(jpeg_image.read()).decode('utf-8')

                    file_path = f'/8/7/{image_name}'

                    data = {
                        "entry": {
                            "id": item["id"],
                            "media_type": item["media_type"],
                            "label": "",
                            "position": item["position"],
                            "disabled": item["disabled"],
                            "types": item["types"],
                            "file": file_path,  # You might need to adjust this path depending on Magento setup
                            "content": {
                                "base64_encoded_data": jpeg_64_encoded,
                                "type": "image/jpeg",
                                "name": image_name
                            }
                        }
                    }

                    media_post_url = f'https://eexera.com/rest/default/V1/products/{product["sku"]}/media/{item["id"]}'

                    response = requests.put(media_post_url, json=data, headers=header)
                print(f'{len(items)} images converted for {product["sku"]} | total : {index} | page : {page}')
                index = index + 1


converter = ImageConverter('default', 'italien')
converter.convert()
