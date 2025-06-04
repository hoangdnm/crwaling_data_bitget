# Bitget Scraper

This project is a Python-based web scraper that utilizes the Pydoll library to extract cryptocurrency data from the Bitget exchange. The scraper is designed to gather information such as prices and other relevant details for various cryptocurrencies.

## Project Structure

```
bitget-scraper
├── src
│   └── scraper.py
├── requirements.txt
└── README.md
```

## Installation

To set up the environment for this project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd bitget-scraper
   ```

2. It is recommended to create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the scraper, execute the following command:

```
python src/scraper.py
```

The scraper will start crawling the Bitget exchange for cryptocurrency data and save the results to an Excel file.

## Dependencies

This project requires the following Python packages:

- Pydoll
- pandas
- openpyxl (for saving data to Excel)

Make sure to install all dependencies listed in `requirements.txt`.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.