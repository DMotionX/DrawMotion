pub mod cli;
pub mod error;
pub mod validators;

use std::process;

fn main() {
    // 1. Get raw input from CLI arguments
    let raw_input = match cli::get_input_args() {
        Ok(input) => input,
        Err(e) => {
            eprintln!("Error: {}", e);
            process::exit(1);
        }
    };

    // 2. Pass input to the string validator
    if let Err(e) = validators::string::validate_input_string(&raw_input) {
        eprintln!("Danger: {}", e);
        process::exit(1);
    }

    // If safe, output success and exit with 0
    println!("Safe");
    process::exit(0);
}
