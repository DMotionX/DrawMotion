use unicode_normalization::UnicodeNormalization;
use crate::error::ScannerError;

pub fn is_safe_char(c: char) -> bool {
    c.is_ascii_alphanumeric()
        || matches!(c, '.' | '_' | '-' | ' ' | '(' | ')')
        || ('\u{0600}'..='\u{06FF}').contains(&c) // Arabic primary
        || ('\u{0750}'..='\u{077F}').contains(&c) // Arabic Supplement
        || ('\u{08A0}'..='\u{08FF}').contains(&c) // Arabic Extended-A
        || ('\u{FB50}'..='\u{FDFF}').contains(&c) // Arabic Presentation Forms-A
        || ('\u{FE70}'..='\u{FEFF}').contains(&c) // Arabic Presentation Forms-B
}

pub fn validate_input_string(raw_input: &str) -> Result<(), ScannerError> {
    // 1. Normalize the Unicode input FIRST (NFKC is stronger than NFC)
    let user_input: String = raw_input.nfkc().collect();
    
    let upper = user_input.to_uppercase();
    let lower = user_input.to_lowercase();

    // 2. Path Traversal Check
    if lower.contains("..") {
        return Err(ScannerError::PathTraversalDetected);
    }

    // 3. Check for Reserved Windows Names
    const RESERVED: &[&str] = &[
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
        "COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³"
    ];
    
    for r in RESERVED {
        let r_dot = format!("{}.", r);
        if upper == *r || user_input == *r || upper.starts_with(&r_dot) || user_input.starts_with(&r_dot) {
            return Err(ScannerError::ReservedNameDetected(r.to_string()));
        }
    }

    // 4. Strict Allowlist character by character
    for c in user_input.chars() {
        if !is_safe_char(c) {
            return Err(ScannerError::IllegalCharacterDetected(c));
        }
    }

    Ok(())
}
