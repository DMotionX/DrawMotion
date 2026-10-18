use std::env;
use crate::error::ScannerError;

pub fn get_input_args() -> Result<String, ScannerError> {
    let args: Vec<String> = env::args().skip(1).collect();
    
    if args.is_empty() {
        return Err(ScannerError::MissingInput);
    }

    // Join arguments into a single raw input string
    Ok(args.join(" "))
}
