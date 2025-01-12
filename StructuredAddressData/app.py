import pandas as pd
import re
import logging
from typing import Dict

class AddressParser:
    def __init__(self):  # Change _init_ to __init__
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)  # Use __name__ for the logger

        
        # Enhanced patterns for better matching
        self.patterns = {
            'building_number': [
                r'D\.?NO:?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'H\.?NO\.?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'HOUSE\s*NO\.?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'NO\.?\s*[-:]?\s*(\d+[A-Za-z0-9/-]*)',
                r'([A-Z]-\d+)',  # For patterns like A-136
                r'(\d+(?:st|nd|rd|th)\s+Floor)',  # For floor numbers
                r'(AP\s*-\s*\d+)',  # For patterns like AP-10
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

    def clean_text(self, text: str) -> str:
        """Clean and standardize input text"""
        text = text.upper()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*,\s*', ', ', text)
        return text.strip()

    def extract_components(self, text: str) -> Dict[str, str]:
        """Extract address components using enhanced regex patterns"""
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
            # Extract postal code
            postal_match = re.search(r'\b\d{6}\b', text)
            if postal_match:
                components['PostalCode'] = postal_match.group()
            
            # Extract state
            state_match = re.search(r'IN-([A-Z]{2})', text)
            if state_match:
                components['State'] = state_match.group(1)
            
            # Extract building number
            for pattern in self.patterns['building_number']:
                match = re.search(pattern, text)
                if match and match.groups():
                    components['BuildingNumber'] = match.group(1)
                    text = text.replace(match.group(1), '')
                    break
            
            # Extract street address
            street_parts = []
            for pattern in self.patterns['street_address']:
                matches = re.finditer(pattern, text)
                for match in matches:
                    street_part = match.group(0).strip()
                    if street_part and street_part not in street_parts:
                        street_parts.append(street_part)
            components['StreetAddress'] = ', '.join(street_parts)
            
            # Extract landmark
            for pattern in self.patterns['landmark']:
                match = re.search(pattern, text)
                if match:
                    if match.groups():
                        components['Landmark'] = match.group(1).strip()
                    else:
                        components['Landmark'] = match.group(0).strip()
                    break
            
            # Extract locality
            for pattern in self.patterns['locality']:
                match = re.search(pattern, text)
                if match:
                    if match.groups():
                        components['Locality'] = match.group(1).strip()
                    else:
                        components['Locality'] = match.group(0).strip()
                    break
            
            # Extract city with safer handling
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
            
            # Default city extraction if not found
            if not city_found:
                city_col = 'Entity.LegalAddress.City'
                if hasattr(self, 'current_row') and city_col in self.current_row and pd.notna(self.current_row[city_col]):
                    components['City'] = str(self.current_row[city_col]).strip().upper()
            
            # Set country
            components['Country'] = 'India'
            
        except Exception as e:
            self.logger.error(f"Error processing address: {str(e)}")
            self.logger.error(f"Problematic text: {text}")
        
        # Clean up any empty or None values
        components = {k: v.strip() if v else '' for k, v in components.items()}
        
        return components

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process a DataFrame containing address columns"""
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
                
                full_address = " ".join([
                    str(row.get(col, '')) for col in address_columns if pd.notna(row.get(col, ''))
                ])
                
                parsed = self.extract_components(full_address)
                parsed_addresses.append(parsed)
                
                elapsed_time = time.time() - start_time
                self.logger.info(f"Processed record {idx + 1} in {elapsed_time:.4f} seconds.")
                
            except Exception as e:
                self.logger.error(f"Error processing row {idx + 1}: {str(e)}")
                parsed_addresses.append({k: '' for k in self.extract_components('').keys()})
        
        return pd.DataFrame(parsed_addresses)

def main():
    try:
        parser = AddressParser()
        
        print("Loading CSV file...")
        input_file = "D:\\UPSC\\INDIA.csv"
        df = pd.read_csv(input_file, low_memory=False)
        
        print(f"Total records in CSV: {len(df)}")
        
        # Process only top 10 records for testing
        df_top10 = df.head(5000)
        print(f"Number of records in df_top10: {len(df_top10)}")
        print("Processing top 10 addresses...")
        
        structured_df = parser.process_dataframe(df_top10)
        
        output_file = "structured_addresses_parsed.csv"
        structured_df.to_csv(output_file, index=False)
        
        print("\nSample of processed addresses:")
        print(structured_df.head().to_string())
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    import time
    main()
