# MMScript

A simple tool to convert Kotak/Kvb Bank statement CSV files into the Realbyte Money Manager format.

## Features

- Converts Kotak Bank CSV statements to Realbyte-compatible CSV
- Handles date, description, and amount formatting
- Easy to use CLI

## Usage

1. Place your Kotak Bank CSV statement in the project directory.
2. Run the converter:

    ```bash
    py csv_to_realbyte.py input.csv output.csv kotak
    ```

3. Import the `output.csv` into Realbyte Money Manager.

## Requirements

- Python 3.x

## Installation

Clone the repository:

## Disclaimer

This tool is not affiliated with Kotak Bank or Realbyte. Use at your own risk.