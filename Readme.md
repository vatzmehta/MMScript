# kotak_to_realbyte_converter

A simple tool to convert Kotak Bank statement CSV files into the Realbyte Money Manager format.

## Features

- Converts Kotak Bank CSV statements to Realbyte-compatible CSV
- Handles date, description, and amount formatting
- Easy to use CLI

## Usage

1. Place your Kotak Bank CSV statement in the project directory.
2. Run the converter:

    ```bash
    py kotak_to_realbyte_converter.py input.csv output.csv
    ```

3. Import the `output.csv` into Realbyte Money Manager.

## Requirements

- Python 3.x

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/kotak_to_realbyte_converter.git
cd kotak_to_realbyte_converter
```

## Disclaimer

This tool is not affiliated with Kotak Bank or Realbyte. Use at your own risk.