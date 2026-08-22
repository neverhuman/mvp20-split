use amphora_assurance_capabilities::deterministic_control_diagnostic;

fn main() {
    let d = deterministic_control_diagnostic("amphora-redteam-audit").unwrap();
    println!("{}", serde_json::to_string_pretty(&d).unwrap());
}
