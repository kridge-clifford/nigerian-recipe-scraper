import requests
from bs4 import BeautifulSoup
import re
import csv
import time
from selenium import Selenium


config = {
    "recipeLinksSelector": "div.entry-content > ul > li > a",
    "recipeTitleSelector": "#content > div.hentry.entry > h1",
    "recipeDirectionSelector": "h2 + ol",
    "details": {
        "recipeIngredientsSelector": "div.entry-content > h2 + ul, div.entry-content > h2 + p + ul",
        "recipeVideoSelector": "div.video-container > iframe",
        "recipeImageSelector": "a > img",
        "recipeMetaDescSelector": "meta[name='description']",
        "recipeRelatedSelector": "p + h3 + ul",
    }
}

quantity_list = ["teaspoon", "tablespoon", "cooking spoons", "stock", "cigar cups", "cooking spoons", "tablespoons",
                 "cups", "small stock", "small party cups", "big stock", "small party cups", "small party cup"]


class Handler(Selenium):
    def __init__(self):
        self.start_time = time.time()
        self.skipped_urls = []
        self.elapse_time = ""
        self.url = "https://www.allnigerianrecipes.com/other/sitemap/"



    @staticmethod
    def json_get(_dict: dict, *keys):
        for key in keys:
            if isinstance(_dict, dict):
                _dict = _dict.get(key, "")
            else:
                return ''
        return _dict



    @staticmethod
    def check_if_url_valid(url):
        url = url.split("com")[1]
        slash_count = url.count("/")
        if "food-ingredients" in url:
            return False
        return True if slash_count > 2 else False



    def run(self):
        recipe_links_selector = self.json_get(config, "recipeLinksSelector")
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, 'html.parser')

        links = soup.select(recipe_links_selector)
        to_csv = []
        for index, link in enumerate(links[30:]):
            recipe_details = self.extract_details(link)
            if not recipe_details:
                continue
            to_csv.append(recipe_details)

        self.elapse_time = str(time.time() - self.start_time)
        self.write_to_csv(to_csv)



    @staticmethod
    def write_to_csv(to_csv):
        with open("output.csv", "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(to_csv)



    def extract_details(self, link):
        recipe_title_selector = self.json_get(config, "recipeTitleSelector")
        recipe_direction_selector = self.json_get(config, "recipeDirectionSelector")
        recipe_details = self.json_get(config, "details")

        recipe_link = link["href"]
        recipe_page = requests.get(recipe_link)
        recipe_soup = BeautifulSoup(recipe_page.content, 'html.parser')
        recipe_title = self.get_selector_text(recipe_title_selector, recipe_soup)

        if not recipe_title or not self.check_if_url_valid(recipe_link):
            self.skipped_urls.append(recipe_link)
            return {}

        recipe_title = recipe_title[0].text

        recipe_direction = self.get_selector_text(recipe_direction_selector, recipe_soup)
        recipe_direction = (recipe_direction[1].text
                            if len(recipe_direction) > 1
                            else recipe_direction[0].text
                            if recipe_direction else "")

        details = self.extract_details_by_selector(recipe_details, recipe_soup)
        recipe_ingredients = (details["recipeIngredientsSelector"] if details["recipeIngredientsSelector"] else "")

        formatted_ingredient = "" if not recipe_ingredients else self.format_ingredients(recipe_ingredients)

        recipe_ingredients = self.get_text(recipe_ingredients)
        recipe_related = self.get_text(details["recipeRelatedSelector"])
        recipe_video = self.get_src(details["recipeVideoSelector"])
        recipe_image = self.get_src(details["recipeImageSelector"])
        recipe_meta_desc = self.get_content(details["recipeMetaDescSelector"])

        recipe_details = [recipe_title, recipe_direction, recipe_ingredients, formatted_ingredient, recipe_link,
                          recipe_related, recipe_video, recipe_image, recipe_meta_desc]

        return recipe_details



    def extract_details_by_selector(self, recipe_details, recipe_soup):
        details = {}
        for key, selector in recipe_details.items():
            text = self.get_selector_one_text(selector, recipe_soup)
            details[key] = text
        return details



    def format_ingredients(self, ingredients):
        formatted_str = ""
        for index, ingredient in enumerate(ingredients.findAll("li")):
            quantity_digit = re.findall(
                    r"^\d+\.\d+[a-zA-Z]{1,3}|^\d+\-\d|^\d{1,3}\½+|^\d{1,3}[a-zA-Z]+|^\d+|^½|^¼", ingredient.text)
            quantity_digit = quantity_digit[0] if quantity_digit else "1"
            quantity_desc = self.find_quantity_match(ingredient.text)
            custom_ingredient = ingredient.text.replace(quantity_digit, "")
            custom_ingredient = custom_ingredient if not quantity_desc else custom_ingredient.replace(quantity_desc, "")
            quantity_final = "{} {}".format(quantity_digit, quantity_desc).strip()
            formatted_str += "quantity:{};customIngredient:{};|".format(quantity_final, custom_ingredient.strip())
            formatted_str = formatted_str if index % 4 == 0 else formatted_str + "\n"
        return formatted_str



    @staticmethod
    def find_quantity_match(ingredient):
        for quantity in quantity_list:
            if quantity in ingredient.lower():
                return quantity
        return ""


if __name__ == '__main__':
    handle = Handler()
    handle.run()
    print("Elapsed time:", handle.elapse_time, "secs.")
    print("Skipped urls:", handle.skipped_urls)
