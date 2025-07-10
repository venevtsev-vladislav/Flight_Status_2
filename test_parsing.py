import re
from datetime import datetime

def parse_flight_request(text: str):
    """Simple flight request parser"""
    clean_text = text.lower().strip()
    
    # Flight number patterns: 2-3 letters + 1-4 digits
    flight_number_pattern = r'\b([a-z]{2,3}\s*\d{1,4})\b'
    flight_match = re.search(flight_number_pattern, clean_text, re.IGNORECASE)
    
    # Date patterns
    today_pattern = r'\b(today|сегодня)\b'
    tomorrow_pattern = r'\b(tomorrow|завтра)\b'
    yesterday_pattern = r'\b(yesterday|вчера)\b'
    date_pattern = r'\b(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})\b'
    
    flight_number = None
    date = None
    
    # Extract flight number
    if flight_match:
        flight_number = flight_match.group(1).replace(' ', '').upper()
    
    # Extract date
    if re.search(today_pattern, clean_text, re.IGNORECASE):
        date = datetime.now().strftime('%Y-%m-%d')
    elif re.search(tomorrow_pattern, clean_text, re.IGNORECASE):
        tomorrow = datetime.now()
        tomorrow = tomorrow.replace(day=tomorrow.day + 1)
        date = tomorrow.strftime('%Y-%m-%d')
    elif re.search(yesterday_pattern, clean_text, re.IGNORECASE):
        yesterday = datetime.now()
        yesterday = yesterday.replace(day=yesterday.day - 1)
        date = yesterday.strftime('%Y-%m-%d')
    elif re.search(date_pattern, clean_text):
        date_match = re.search(date_pattern, clean_text)
        if date_match:
            date_str = date_match.group(1).replace('/', '.').replace('-', '.')
            parts = date_str.split('.')
            if len(parts) == 3:
                day = parts[0].zfill(2)
                month = parts[1].zfill(2)
                year = parts[2] if len(parts[2]) == 4 else '20' + parts[2]
                date = f"{year}-{month}-{day}"
    
    return {
        'flight_number': flight_number,
        'date': date,
        'confidence': 0.8 if flight_number or date else 0
    }

# Test cases
test_cases = [
    "VA6042 07.07.2025",
    "VA6042 сегодня",
    "VA6042 завтра",
    "VA6042",
    "07.07.2025",
    "просто текст"
]

print("Testing flight parsing:")
for test in test_cases:
    result = parse_flight_request(test)
    print(f"'{test}' -> {result}") 