import re

def clean_title(title):
    """Clean and normalize the track title for better search results."""
    if not title:
        return ""
        
    patterns_to_remove = [
        r'\s*\(.*lyric.*\)',
        r'\s*\[.*\]',
        r'\s*\(.*official.*\)',
        r'\s*\(?official.*video\)?',
        r'\s*\(?official.*audio\)?',
        r'\b(HD|HQ|4K|1080p|720p)\b',
        r'\s*[-–]\s*(lyrics?|official|video|audio|HD|HQ|4K|1080p|720p).*$',
        r'\s*\([^)]*[α-ωΑ-Ω][^)]*\)',
        r'\[.*[α-ωΑ-Ω].*\]',
    ]
    
    cleaned = title.strip()
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def greek_to_greeklish(text):
    """Convert Greek characters to Greeklish."""
    if not text:
        return ""
        
    greek_to_greeklish_map = {
        'α': 'a', 'ά': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'έ': 'e',
        'ζ': 'z', 'η': 'i', 'ή': 'i', 'θ': 'th', 'ι': 'i', 'ί': 'i', 'ϊ': 'i',
        'ΐ': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
        'ό': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y',
        'ύ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o', 'ώ': 'o',
        'Α': 'A', 'Ά': 'A', 'Β': 'V', 'Γ': 'G', 'Δ': 'D', 'Ε': 'E', 'Έ': 'E',
        'Ζ': 'Z', 'Η': 'I', 'Ή': 'I', 'Θ': 'Th', 'Ι': 'I', 'Ί': 'I', 'Ϊ': 'I',
        'Κ': 'K', 'Λ': 'L', 'Μ': 'M', 'Ν': 'N', 'Ξ': 'X', 'Ο': 'O', 'Ό': 'O',
        'Π': 'P', 'Ρ': 'R', 'Σ': 'S', 'Τ': 'T', 'Υ': 'Y', 'Ύ': 'Y', 'Φ': 'F',
        'Χ': 'Ch', 'Ψ': 'Ps', 'Ω': 'O', 'Ώ': 'O'
    }
    
    return ''.join(greek_to_greeklish_map.get(c, c) for c in text)
