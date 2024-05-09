import json
from datetime import datetime

import requests
import openai
from dotenv import load_dotenv
from openai import OpenAI

# openai.api_key = "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"
load_dotenv()


class MagentoMetas:

    def __init__(self, site_id, language) -> None:
        self.site_id = site_id
        self.site_language = language
        self.token_url = f'https://eexera.com/rest/{self.site_id}/V1/integration/admin/token'
        self.page_size = 100
        self.product_total = 131047
        self.iterations = 1311
        self.products_current_page = 1
        self.get_products_url = f'https://eexera.com/rest/{self.site_id}/V1/products'
        self.credentials = {"username": "yassinelfarhi", "password": "Yassinelfarhi2023?"}
        self.token = self.get_token()  # this token is valable for 4 hours
        self.client = OpenAI()

    def get_token(self) -> str:
        try:
            response = requests.post(self.token_url, json=self.credentials)
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError("Could not get token :" + response.status_code)

        except:
            raise Exception

    def metas(self):
        index = 0
        for i in range(75, 1310):
            page = i + 1
            self.token = self.get_token()
            products_chunk = self.get_products_chunk(page, self.page_size)

            # filtred_products_chunk = self.filter_products(products_chunk)
            for product in products_chunk:
                # filtred_products.append(product)
                meta_title = self.meta_title(product["title"])
                meta_description = self.meta_description(product["title"])
                meta_keywords = self.meta_keywords(product["title"])
                index = index + 1
                try:
                    headers = {'Authorization': f'Bearer {self.token}'}
                    attributes = {
                        "product": {
                            "custom_attributes": [
                                {"attribute_code": "meta_title", "value": meta_title},
                                {"attribute_code": "meta_description", "value": meta_description},
                                {"attribute_code": "meta_keyword", "value": meta_keywords}
                            ]
                        }
                    }
                    print("sku : " + product["sku"] + " | total :" + str(index))
                    # print(json.dumps([index, meta_title, meta_description, meta_keywords]))
                    # print(attributes)
                    put_url = self.get_products_url + "/" + product['sku']
                    response = requests.put(put_url, headers=headers, json=attributes)
                    if index == 50:
                        return
                except Exception as e:
                    print(e)

    def get_products_chunk(self, page, size):
        try:
            params = {"searchCriteria[page_size]": str(size), "searchCriteria[currentPage]": str(page)}
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(self.get_products_url, headers=headers, params=params)

            # print(response.status_code)
            # print(json_response['items'][0])
            # print(self.get_products_url)
            # return
            if response.status_code == 200:
                json_response = response.json()
                products = json_response['items']
                # print(json_response)
                products_list = [
                    {"title": product['name'], "sku": product['sku'], "custom_attributes": product['custom_attributes']}
                    for product in products]
                return products_list
                # return response.json()
            else:
                raise ValueError("Couldn't fetch products / error code :" + response.status_code)
        except Exception as e:
            print(e)

    def meta_title(self, product_title):
        prompt = "generate a unique optimized seo meta title for this product [" + product_title + "] written in " + self.site_language + " ; the title should be limited to 60 characters , have Eexera brand on it and includes a call to action;"
        completion = self.client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=200
        )
        return completion.choices[0].text.replace("\n", '').replace('"', '')

    def meta_description(self, product_title):
        prompt = "generate a unique optimized seo meta description for this product [" + product_title + "] written in " + self.site_language + " ; the description should be limited to 160 characters ,have Eexera brand on it and includes a call to action;"
        completion = self.client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=200
        )
        return completion.choices[0].text.replace("\n", '').replace('"', '')

    def meta_keywords(self, product_title):
        prompt = "generate comma separated meta keywords for this product [" + product_title + "] written in " + self.site_language + " ,the keywords should be unique , optimized for seo and limited to 10 keywords"
        completion = self.client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=200
        )
        return completion.choices[0].text.replace("\n", '').replace('"', '')

    # filter products with no metafields
    def filter_products(self, products):
        filtred_products = []
        for product in products:
            append = True
            for custom_attribute in product['custom_attributes']:
                if custom_attribute['attribute_code'] in ["meta_title", "meta_keyword", "meta_description"] and \
                        custom_attribute['value']:
                    append = False

            if append:
                filtred_products.append(product)

        return filtred_products
