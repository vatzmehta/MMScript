# Realbyte MoneyMager Import Script

A simple tool to convert Bank statement CSV files into the Realbyte Money Manager Bulk Import format.

"bank statement to realbyte money manager format"

## Features

- Converts Bank CSV statements to Realbyte-compatible CSV
- Handles date, description, amount formatting.
- Has support for auto categorization and auto sub-categorization
- Easy to use CLI
- Support for 
    -   Kotak Bank
    -   Karur Vysya Bank (KVB)
    -   Axis Credit Card Statement

## Usage

1. Place your Bank CSV statement in the project directory.
2. Run the converter:

    ```bash
    py csv_to_realbyte.py input.csv output.csv kotak
    ```

3. Import the `output.csv` into Realbyte Money Manager using import csv function inside backup.

## Requirements

- Python 3.x

## Installation

Clone the repository and run locally

## Disclaimer

This tool is not affiliated with Kotak Bank or Realbyte. Use at your own risk.
