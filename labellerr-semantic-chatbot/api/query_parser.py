# api/query_parser.py
import re
from typing import Dict, List, Optional

def parse_temporal_query(query: str) -> Dict[str, Optional[str]]:
    """Extract month from queries like 'product update may 2025'"""
    query_lower = query.lower()
    
    # Month patterns
    months = {
        'january': '01', 'jan': '01', 'february': '02', 'feb': '02',
        'march': '03', 'mar': '03', 'april': '04', 'apr': '04',
        'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
        'august': '08', 'aug': '08', 'september': '09', 'sep': '09',
        'october': '10', 'oct': '10', 'november': '11', 'nov': '11',
        'december': '12', 'dec': '12'
    }
    
    month = None
    year = None
    
    # Find year
    year_match = re.search(r'20\d{2}', query_lower)
    if year_match:
        year = year_match.group()
    
    # Find month
    for month_name, month_num in months.items():
        if month_name in query_lower:
            month = month_num
            break
    
    # Combine if both found
    if year and month:
        return {"month": f"{year}-{month}"}
    
    return {"month": None}

def extract_keywords(query: str) -> List[str]:
    """Extract product update related keywords"""
    keywords = []
    query_lower = query.lower()
    
    keyword_map = {
        "product": ["product"],
        "update": ["update", "updates"],
        "release": ["release", "releases", "released"],
        "changelog": ["changelog", "change log"],
        "announcement": ["announcement", "announce"],
        "whats-new": ["what's new", "whats new", "new features"],
        "feature": ["feature", "features"]
    }
    
    for category, terms in keyword_map.items():
        if any(term in query_lower for term in terms):
            keywords.append(category)
    
    return list(set(keywords))  # Remove duplicates