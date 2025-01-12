import pandas as pd
import re
import logging
import time
import os
from typing import Dict

class AddressParser:
    def _init_(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Original patterns dictionary remains the same
        self.patterns = {
            'building_number': [
                r'D\.?NO:?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'H\.?NO\.?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'HOUSE\s*NO\.?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'NO\.?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'([A-Z]-\d+)',
                r'(\d+(?:st|nd|rd|th)\s+Floor)',
                r'(AP\s*-\s*\d+)',
            ],
            'street_address': [
                r'(?:ROAD|RD)(?:[^,]*?)(?=,|\s+(?:NEAR|BEHIND|OPPOSITE|LANDMARK|NAGAR|COLONY|ENCLAVE|PHASE|SECTOR|$))',
                r'(?:STREET|ST)(?:[^,]*?)(?=,|\s+(?:NEAR|BEHIND|OPPOSITE|LANDMARK|NAGAR|COLONY|ENCLAVE|PHASE|SECTOR|$))',
                r'(?:LANE)(?:[^,]*?)(?=,|\s+(?:NEAR|BEHIND|OPPOSITE|LANDMARK|NAGAR|COLONY|ENCLAVE|PHASE|SECTOR|$))',
                r'(?:CROSS|CROSS ROAD)(?:[^,]*?)(?=,|\s+(?:NEAR|BEHIND|OPPOSITE|LANDMARK|NAGAR|COLONY|ENCLAVE|PHASE|SECTOR|$))',
                r'SECTOR[^,]+',
                r'S\.F\.No:[^,]+',
            ],
            'landmark': [
                r'NEAR\s+([^,]+)',
                r'OPPOSITE\s+([^,]+)',
                r'BEHIND\s+([^,]+)',
                r'LANDMARK[S]?\s+([^,]+)',
                r'(?:DLF|SEZ)[^,]+',
            ],
            'locality': [
                r'([^,]+(?:NAGAR|COLONY|ENCLAVE|PHASE|EXTENSION))[^,]*',
                r'(?:SECTOR|SEC)[^,]+',
                r'(?:PHASE|PH)[^,]+',
                r'(?:BLOCK)[^,]+',
            ],
            'city': [
                r'(?:DISTRICT|DIST|TALUK|TEHSIL)\s*[-:]?\s*([^,]+)',
                r'\b(?:NEW DELHI|DELHI|MUMBAI|BANGALORE|CHENNAI|KOLKATA|HYDERABAD|GURUGRAM|NOIDA|PUNE|AHMEDABAD|JAIPUR|SURAT|LUCKNOW|KANPUR|NAGPUR|INDORE|THANE|BHOPAL|VISAKHAPATNAM|PIMPRI-CHINCHWAD|PATNA|VADODARA|GHAZIABAD|LUDHIANA|AGRA|NASHIK|FARIDABAD|MEERUT|RAJKOT|KALYAN-DOMBIVALI|VASAI-VIRAR|VARANASI|SRINAGAR|AURANGABAD|DHANBAD|AMRITSAR|NAVI MUMBAI|ALLAHABAD|RANCHI|HOWRAH|JABALPUR|GWALIOR|VIJAYAWADA|JODHPUR|MADURAI|RAIPUR|KOTA|GUWAHATI|CHANDIGARH|SOLAPUR|HUBLI-DHARWAD|BAREILLY|MORADABAD|MYSORE|GURGAON|ALIGARH|JALANDHAR|TIRUCHIRAPPALLI|BHUBANESWAR|SALEM|MIRA-BHAYANDAR|THIRUVANANTHAPURAM|BHIWANDI|SAHARANPUR|GORAKHPUR|GUNTUR|BIKANER|AMRAVATI|NOIDA|JAMSHEDPUR|BHILAI|CUTTACK|FIROZABAD|KOCHI|NELLORE|BHAVNAGAR|DEHRADUN|DURGAPUR|ASANSOL|ROURKELA|NANDED|KOLHAPUR|AJMER|AKOLA|GULBARGA|JAMNAGAR|UJJAIN|LONI|SILIGURI|JHANSI|ULHASNAGAR|JAMMU|SANGLI-MIRAJ|MANGALORE|ERODE|BELGAUM|AMBATTUR|TIRUNELVELI|MALEGAON|GAYA|JALGAON|UDAIPUR|MAHESHTALA)\b'
            ]
        }

    # Original methods remain the same
    def clean_text(self, text: str) -> str:
        text = text.upper()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*,\s*', ', ', text)
        return text.strip()

    def extract_components(self, text: str) -> Dict[str, str]:
        # Original extract_components method remains the same
        text = self.clean_text(text)
        components = {
            'BuildingNumber': '',
            'StreetAddress': '',
            'Landmark': '',
            'Locality': '',
            'City': '',
            'State': '',
            'PostalCode': '',
            'Country': ''
        }

        try:
            postal_match = re.search(r'\b\d{6}\b', text)
            if postal_match:
                components['PostalCode'] = postal_match.group()

            state_match = re.search(r'IN-([A-Z]{2})', text)
            if state_match:
                components['State'] = state_match.group(1)

            for pattern in self.patterns['building_number']:
                match = re.search(pattern, text)
                if match and match.groups():
                    components['BuildingNumber'] = match.group(1)
                    text = text.replace(match.group(1), '')
                    break

            street_parts = []
            for pattern in self.patterns['street_address']:
                matches = re.finditer(pattern, text)
                for match in matches:
                    street_part = match.group(0).strip()
                    if street_part and street_part not in street_parts:
                        street_parts.append(street_part)
            components['StreetAddress'] = ', '.join(street_parts)

            for pattern in self.patterns['landmark']:
                match = re.search(pattern, text)
                if match:
                    if match.groups():
                        components['Landmark'] = match.group(1).strip()
                    else:
                        components['Landmark'] = match.group(0).strip()
                    break

            for pattern in self.patterns['locality']:
                match = re.search(pattern, text)
                if match:
                    if match.groups():
                        components['Locality'] = match.group(1).strip()
                    else:
                        components['Locality'] = match.group(0).strip()
                    break

            city_found = False
            for pattern in self.patterns['city']:
                match = re.search(pattern, text)
                if match:
                    if match.groups():
                        components['City'] = match.group(1).strip()
                    else:
                        components['City'] = match.group(0).strip()
                    city_found = True
                    break

            if not city_found:
                city_col = 'Entity.LegalAddress.City'
                if hasattr(self, 'current_row') and city_col in self.current_row and pd.notna(self.current_row[city_col]):
                    components['City'] = str(self.current_row[city_col]).strip().upper()

            components['Country'] = 'India'

        except Exception as e:
            self.logger.error(f"Error processing address: {str(e)}")
            self.logger.error(f"Problematic text: {text}")

        components = {k: v.strip() if v else '' for k, v in components.items()}
        return components

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        # Original process_dataframe method remains the same
        self.logger.info(f"Number of rows received in process_dataframe: {len(df)}")

        address_columns = [
            'Entity.LegalAddress.FirstAddressLine',
            'Entity.LegalAddress.AdditionalAddressLine.1',
            'Entity.LegalAddress.AdditionalAddressLine.2',
            'Entity.LegalAddress.AdditionalAddressLine.3',
            'Entity.LegalAddress.City',
            'Entity.LegalAddress.Region',
            'Entity.LegalAddress.Country',
            'Entity.LegalAddress.PostalCode'
        ]

        parsed_addresses = []

        for idx, row in df.iterrows():
            try:
                self.logger.info(f"Starting to process record {idx + 1}")
                start_time = time.time()

                self.current_row = row
                full_address = " ".join([str(row.get(col, '')) for col in address_columns if pd.notna(row.get(col, ''))])
                parsed = self.extract_components(full_address)
                parsed_addresses.append(parsed)

                elapsed_time = time.time() - start_time
                self.logger.info(f"Processed record {idx + 1} in {elapsed_time:.4f} seconds.")

            except Exception as e:
                self.logger.error(f"Error processing row {idx + 1}: {str(e)}")
                parsed_addresses.append({k: '' for k in self.extract_components('').keys()})

        return pd.DataFrame(parsed_addresses)

def process_file(file_number: str, sample_size: int = 5000):
    try:
        parser = AddressParser()
        
        # Create directories if they don't exist
        os.makedirs("data/input", exist_ok=True)
        os.makedirs("data/output", exist_ok=True)
        
        input_file = f"data/input/{file_number}.csv"
        print(f"Processing file: {input_file}")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file {input_file} not found")
            
        df = pd.read_csv(input_file, low_memory=False)
        print(f"Total records in CSV: {len(df)}")

        df_sample = df.head(sample_size)
        print(f"Processing {sample_size} records...")

        structured_df = parser.process_dataframe(df_sample)

        output_file = f"data/output/structured_addresses_{file_number}.csv"
        structured_df.to_csv(output_file, index=False)

        print(f"Results saved to {output_file}")
        return structured_df

    except Exception as e:
        print(f"Error processing file {file_number}: {str(e)}")
        return None

if __name__ == "_main_":
    import sys
    
    if len(sys.argv) > 1:
        file_number = sys.argv[1]  # Accept file number as command line argument
        df = process_file(file_number)
        if df is not None:
            print("\nSample of processed addresses:")
            print(df.head().to_string())
    else:
        print("Please provide a file number (e.g., python script.py 16)")