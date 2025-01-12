import pandas as pd
from transformers import AutoTokenizer, LlamaForTokenClassification
import torch
import re
import json
from typing import List, Dict, Tuple
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import requests
from tqdm import tqdm

class AddressParser:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.geocoder = Nominatim(
            user_agent="address_parser_india",
            timeout=10
        )

        self.pincode_cache = {}
        self.geocoding_cache = {}
        self.initialize_state_mapping()

    def initialize_state_mapping(self):
        """Initialize comprehensive mapping of state codes and names"""
        self.state_mapping = {
            'ANDHRA PRADESH': ['AP', 'ANDHRA', 'A.P.'],
            'ARUNACHAL PRADESH': ['AR', 'ARUNACHAL'],
            'ASSAM': ['AS'],
            'BIHAR': ['BR'],
            'CHHATTISGARH': ['CG', 'CT'],
            'GOA': ['GA'],
            'GUJARAT': ['GJ'],
            'HARYANA': ['HR'],
            'HIMACHAL PRADESH': ['HP'],
            'JHARKHAND': ['JH'],
            'KARNATAKA': ['KA', 'KAR'],
            'KERALA': ['KL', 'KER'],
            'MADHYA PRADESH': ['MP'],
            'MAHARASHTRA': ['MH', 'MAHA'],
            'MANIPUR': ['MN'],
            'MEGHALAYA': ['ML'],
            'MIZORAM': ['MZ'],
            'NAGALAND': ['NL'],
            'ODISHA': ['OR', 'OD'],
            'PUNJAB': ['PB'],
            'RAJASTHAN': ['RJ'],
            'SIKKIM': ['SK'],
            'TAMIL NADU': ['TN', 'TAMILNADU', 'T.N.'],
            'TELANGANA': ['TS', 'TG', 'TELENGANA'],
            'TRIPURA': ['TR'],
            'UTTAR PRADESH': ['UP'],
            'UTTARAKHAND': ['UK', 'UA'],
            'WEST BENGAL': ['WB'],
            'DELHI': ['DL', 'NCT', 'NCT OF DELHI', 'DELHI NCT'],
            'JAMMU AND KASHMIR': ['JK'],
            'LADAKH': ['LA'],
            'PUDUCHERRY': ['PY', 'PONDICHERRY'],
            'ANDAMAN AND NICOBAR ISLANDS': ['AN'],
            'CHANDIGARH': ['CH'],
            'DADRA AND NAGAR HAVELI AND DAMAN AND DIU': ['DN', 'DD'],
            'LAKSHADWEEP': ['LD']
        }

        # Create reverse mapping
        self.state_code_to_name = {}
        for state, codes in self.state_mapping.items():
            for code in codes:
                self.state_code_to_name[code.upper()] = state
            # Also map the full name to itself
            self.state_code_to_name[state] = state

    def clean_value(self, value) -> str:
        """Clean and validate input values"""
        if pd.isna(value) or value is None:
            return ''
        return str(value).strip()

    def convert_state_code(self, state_code: str) -> str:
        """Convert state code to full state name"""
        if not state_code:
            return ''

        state_upper = state_code.upper().strip()

        # Check direct mapping
        if state_upper in self.state_code_to_name:
            return self.state_code_to_name[state_upper]

        # Check if it's already a full state name
        for full_name in self.state_mapping.keys():
            if state_upper == full_name:
                return full_name

        # Check variations
        for full_name, variations in self.state_mapping.items():
            if state_upper in variations:
                return full_name

        return state_code  # Return original if no mapping found

    def process_address(self, row: pd.Series) -> Dict[str, str]:
        """Process a single address with specific fields"""
        result = {
            'BuildingNumber': self.clean_value(row.get('BuildingNumber', '')),
            'StreetName': self.clean_value(row.get('StreetAddress', '')),
            'TownName': self.clean_value(row.get('City', '')),
            'CountrySubDivision': self.convert_state_code(self.clean_value(row.get('State', ''))),
            'PostCode': self.clean_value(row.get('PostalCode', '')),
            'Country': 'INDIA' if self.clean_value(row.get('Country', 'IN')).upper() in ['IN', 'IND', 'INDIA'] else self.clean_value(row.get('Country', 'IN'))
        }

        # Try to get additional info from PIN code if available
        if result['PostCode'] and not (result['TownName'] or result['CountrySubDivision']):
            pincode_info = self.get_location_from_pincode(result['PostCode'])
            if pincode_info:
                if not result['TownName']:
                    result['TownName'] = pincode_info['city']
                if not result['CountrySubDivision']:
                    result['CountrySubDivision'] = self.convert_state_code(pincode_info['state'])

        return result

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process entire DataFrame with progress tracking"""
        results = []

        with tqdm(total=len(df), desc="Processing addresses") as pbar:
            for _, row in df.iterrows():
                try:
                    processed_address = self.process_address(row)
                    results.append(processed_address)
                except Exception as e:
                    self.logger.error(f"Error processing row: {row}")
                    self.logger.error(str(e))
                    results.append({
                        'BuildingNumber': '',
                        'StreetName': '',
                        'TownName': '',
                        'CountrySubDivision': '',
                        'PostCode': '',
                        'Country': 'INDIA'
                    })
                pbar.update(1)

        result_df = pd.DataFrame(results)

        # Calculate and display completion statistics
        completion_stats = self.calculate_completion_stats(result_df)
        self.display_stats(completion_stats)

        return result_df

    def calculate_completion_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate completion statistics for each field"""
        stats = {}
        for column in df.columns:
            completion_rate = (df[column].notna() & (df[column] != '')).mean() * 100
            stats[column] = completion_rate
        return stats

    def display_stats(self, stats: Dict[str, float]):
        """Display completion statistics"""
        print("\nField Completion Rates:")
        print("-" * 40)
        for field, rate in stats.items():
            print(f"{field:15s}: {rate:6.2f}%")

def main():
    try:
        parser = AddressParser()

        input_file = "D:/UPSC/data/output/structured_addresses.csv"
        df = pd.read_csv(input_file)

        print(f"Processing {len(df)} addresses...")

        result_df = parser.process_dataframe(df)

        output_file = "D:/UPSC/data_output/addresses.csv"
        result_df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")

        print("\nSample processed addresses:")
        print(result_df.head().to_string())

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        logging.error(f"Error in main execution: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
