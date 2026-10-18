use std::fmt;

#[derive(Debug)]
pub enum ScannerError {
    MissingInput,
    PathTraversalDetected,
    ReservedNameDetected(String),
    IllegalCharacterDetected(char),
}

impl fmt::Display for ScannerError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ScannerError::MissingInput => write!(f, "Missing input to scan."),
            ScannerError::PathTraversalDetected => write!(f, "Path traversal detected"),
            ScannerError::ReservedNameDetected(name) => write!(f, "Reserved Windows name detected: {}", name),
            ScannerError::IllegalCharacterDetected(c) => write!(f, "Illegal character detected: {:?}", c),
        }
    }
}
