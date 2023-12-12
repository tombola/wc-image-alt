# SPDX-FileCopyrightText: 2023-present tombola <tombola@github>
#
# SPDX-License-Identifier: MIT
import click
import os
import requests

from wc_image_alt.__about__ import __version__
from woocommerce import API
from rich import print

WC_URL = os.environ.get("WC_URL")
WC_CONSUMER_KEY = os.environ.get("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.environ.get("WC_CONSUMER_SECRET")

WC_MAX_API_RESULT_COUNT = 100


def get_wcapi() -> API:
    if not all(
        (
            WC_URL,
            WC_CONSUMER_KEY,
            WC_CONSUMER_SECRET,
        )
    ):
        print("Credentials not provided from environment")
        quit()
    return API(
        url=WC_URL,
        consumer_key=WC_CONSUMER_KEY,
        consumer_secret=WC_CONSUMER_SECRET,
        version="wc/v3",
        timeout=30,
    )


def wcapi(func, *args, **kwargs):
    def wrapper():
        return func(wcapi=get_wcapi(), *args, **kwargs)

    return wrapper


def aggregate_paginated_response(func):
    """
    Repeat calls a decorated function to get all pages of WooCommerce API response.

    Combines the response data into a single list.

    Function to call must accept parameters:
        - wcapi object
        - page number
    """

    def wrapper(page=0, *args, **kwargs):
        items = []
        page = 0
        num_pages = WC_MAX_API_RESULT_COUNT

        while page < num_pages:
            page += 1
            print(f"{page=}")

            response = func(page=page, *args, **kwargs)

            items.extend(response.json())
            num_pages = int(response.headers["X-WP-TotalPages"])
            num_products = int(response.headers["X-WP-Total"])

        print(f"{num_products=}, {len(items)=}")
        return items

    return wrapper


@wcapi
@aggregate_paginated_response
def get_all_products(wcapi: API, page=1) -> requests.Response:
    """
    Query WooCommerce rest api for all products

    Iterates paginated requests to escape API max per page limit.
    """
    response = wcapi.get(
        "products",
        params={
            "per_page": WC_MAX_API_RESULT_COUNT,
            "page": page,
        },
    )
    # response = wcapi.get(
    #     "products",
    # )
    print(response.status_code)
    response.raise_for_status()
    return response


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.option("--force", "-f", is_flag=True)
@click.version_option(version=__version__, prog_name="wc-image-alt")
def wc_image_alt(force):
    if force or click.confirm(f'Querying {WC_URL} - continue?'):
        click.echo("Getting products from WooCommerce")
    else:
        click.echo("Goodbye")

    response: requests.Response = get_all_products()

    try:
        products = response.json()
    except Exception:
        exit(1)

    print(f"{len(products)} products returned")
