#
# SPDX-FileCopyrightText: 2023-present tombola <tombola@github>
# SPDX-License-Identifier: MIT
import click
import os
import requests
import csv
from functools import wraps

from rich.console import Console
from rich.table import Table

from wc_image_alt.__about__ import __version__
from woocommerce import API

WC_URL = os.environ.get("WC_URL")
WC_CONSUMER_KEY = os.environ.get("WC_CONSUMER_KEY")
WC_CONSUMER_SECRET = os.environ.get("WC_CONSUMER_SECRET")
WC_PRODUCTION_ENVIRONMENT = os.environ.get("WC_PRODUCTION_ENVIRONMENT")


WC_MAX_API_RESULT_COUNT = 100
CSV_OUTPUT_FILE = "product_images.csv"

console = Console()


def get_wcapi() -> API:
    if not all(
        (
            WC_URL,
            WC_CONSUMER_KEY,
            WC_CONSUMER_SECRET,
        )
    ):
        console.print("Credentials not provided from environment")
        quit()
    console.print("Connecting to {WC_URL}")
    return API(
        url=WC_URL,
        consumer_key=WC_CONSUMER_KEY,
        consumer_secret=WC_CONSUMER_SECRET,
        version="wc/v3",
        timeout=30,
    )


def wcapi(func):
    def wrapper(*args, **kwargs):
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
            console.print(f"{page=}")

            response = func(page=page, *args, **kwargs)

            items.extend(response.json())
            num_pages = int(response.headers["X-WP-TotalPages"])
            num_products = int(response.headers["X-WP-Total"])

        console.print(f"{num_products=}, {len(items)=}")
        return items

    return wrapper


@wcapi
@aggregate_paginated_response
def get_all_products(wcapi: API, page=1) -> requests.Response:
    """
    Query WooCommerce rest api for all products

    Iterates paginated requests to escape API max per page limit.
    """
    # TODO: yield request and combine to aggregate, rather than decorator
    response = wcapi.get(
        "products",
        params={
            "per_page": WC_MAX_API_RESULT_COUNT,
            "page": page,
        },
    )

    console.print(response.status_code)
    response.raise_for_status()
    return response


def get_alt_suggestion(product):
    alt = product["name"].split("***")[0].split("(")[0]
    # change word order from hyphen
    hyphenated = alt.split(" - ")
    if len(hyphenated) == 2:
        alt = f"{hyphenated[1]}{hyphenated[0]}"
    # strip quotes to avoid issues?
    return alt


@wcapi
def get_products(wcapi: API, num=0) -> dict:
    """
    Query WooCommerce rest api for specified number of products
    """
    # TODO: Not working!
    response = wcapi.get(
        "products",
        params={
            "per_page": num,
        },
    )
    console.print(response.status_code)
    response.raise_for_status()
    return response.json()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--force", "-f", is_flag=True)
@click.option("--write", "-w", is_flag=True)
@click.version_option(version=__version__, prog_name="wc-image-alt")
@click.pass_context
def cli(ctx, write, force):
    ctx.ensure_object(dict)
    ctx.obj["write"] = write
    ctx.obj["force"] = force


@cli.command()
@click.option("-n", "--rows", type=click.INT, default=0)
@click.pass_context
def export_all(ctx, rows, *args, **kwargs):
    force = ctx.parent.obj["force"]
    write = ctx.parent.obj["write"]
    console.log(f"{force=} {write=}")

    if WC_PRODUCTION_ENVIRONMENT:
        force = False

    if force or click.confirm(f'Querying {WC_URL} - continue?'):
        click.echo("Getting products from WooCommerce")
    else:
        click.echo("Goodbye")
        exit(1)

    if rows:
        products = get_products(num=rows)
    else:
        products = get_all_products()

    table = Table(title="Product Images")
    table.add_column("Product name", justify="right", style="cyan", no_wrap=True)
    table.add_column("Image name", style="magenta")
    table.add_column("Alt", justify="right", style="green")
    table.add_column("Suggested", justify="right", style="green")
    table.add_column("Src", style="cyan")
    table.add_column("Product", style="blue")
    table.add_column("Product ID", style="blue")
    table.add_column("Image ID", style="blue")

    with open(CSV_OUTPUT_FILE, mode='w') as product_images_csv:
        images_csv = csv.writer(product_images_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        images_csv.writerow(
            (
                "Product name",
                "Image name",
                "Alt",
                "Suggested",
                "Src",
                "Product",
                "Product ID",
                "Image ID",
            )
        )
        for product in products:
            images = product["images"]
            for image in images:
                row = (
                    product["name"],
                    image["name"],
                    image["alt"],
                    get_alt_suggestion(product),
                    image["src"],
                    product["permalink"],
                    str(product["id"]),
                    str(image["id"]),
                )
                table.add_row(*row)
                images_csv.writerow(row)

    console.print(table)
    console.print(f"{len(products)} products returned")
    console.print(f"Exported to {CSV_OUTPUT_FILE}")
