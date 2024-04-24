import json
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.firefox.service import Service
from selenium import webdriver

pages_count = 4


def extract_price(wrapper, css_class):
    price_element = wrapper.find("span", {"class": css_class})
    return price_element.text if price_element else ""


def get_product_data(product):
    product_id = product.get("id")
    product_link = product.find("a").get("href")
    product_link = f"https://online.metro-cc.ru{product_link}"

    product_unit_prices = product.find("div", {"class": "product-unit-prices__actual-wrapper"})
    sale_price = extract_price(product_unit_prices, "product-price__sum-rubles") + \
                 extract_price(product_unit_prices, "product-price__sum-penny")
    sale_price = f"{sale_price} Р/шт" if sale_price else ""

    product_unit_prices_old = product.find("div", {"class": "product-unit-prices__old-wrapper"})
    standard_price = extract_price(product_unit_prices_old, "product-price__sum-rubles") + \
                     extract_price(product_unit_prices_old, "product-price__sum-penny")
    standard_price = f"{standard_price} Р/шт" if standard_price else ""

    if not standard_price:
        sale_price, standard_price = "", sale_price

    req = requests.get(product_link)
    soup = BeautifulSoup(req.text, "lxml")

    product_name = soup.find("h1",
                             {"class": "product-page-content__product-name catalog-heading heading__h2"}).find(
        "span").text.strip()

    product_attributes = soup.find("div", {
        "class": "product-attributes product-page-content__attributes-short style--product-page-short-list"}).find_all(
        "li", {"class": "product-attributes__list-item"})

    product_brand = ""
    for attribute in product_attributes:
        if attribute.find("span", {"class": "product-attributes__list-item-name-text"}).text.strip() == "Бренд":
            product_brand = attribute.find("a").text.strip()

    return {
        "id": product_id,
        "name": product_name,
        "link": product_link,
        "sale_price": sale_price,
        "standard_price": standard_price,
        "brand": product_brand
    }


def get_data(url):
    products_result = {}
    service = Service(executable_path="geckodriver")
    product_number = 1

    for page in range(1, pages_count + 1):
        full_page = f"{url}{page}"
        driver = webdriver.Firefox(service=service)
        driver.get(full_page)
        soup = BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

        products = soup.find_all("div", {"class": ["product-card", "subcategory-or-type__products-item"]})

        for product in products:
            product_dict = get_product_data(product)
            products_result[f"product_{product_number}"] = product_dict
            product_number += 1

    return products_result


def main():
    result = get_data(
        "https://online.metro-cc.ru/category/bezalkogolnye-napitki/pityevaya-voda-kulery?from=under_search&page=")
    with open("products_data.json", "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
