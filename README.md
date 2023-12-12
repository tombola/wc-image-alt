# wc-image-alt

[![PyPI - Version](https://img.shields.io/pypi/v/wc-image-alt.svg)](https://pypi.org/project/wc-image-alt)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wc-image-alt.svg)](https://pypi.org/project/wc-image-alt)

-----

**Table of Contents**

- [wc-image-alt](#wc-image-alt)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Export a CSV of product images](#export-a-csv-of-product-images)
    - [Import alt text into WooCommerce](#import-alt-text-into-woocommerce)
  - [License](#license)

## Installation

```console
pip install wc-image-alt
```

## Usage

First copy `.env.example` to `env` and fill in your woocommerce REST API
credentials.

Either load this using dotenv, or source the file (`source .env`).

### Export a CSV of product images

`wc-image-alt export-csv`

### Import alt text into WooCommerce

Dry run:

`wc-image-alt import-csv`

Update the product image alt text from the (exported/modified) CSV:

`wc-image-alt -w import-csv`


## License

`wc-image-alt` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
