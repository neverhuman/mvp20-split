fn main() {
    let path = std::env::args()
        .nth(1)
        .expect("usage: stable_hash PATH [JSON_POINTER]");
    let pointer = std::env::args().nth(2);
    let bytes = std::fs::read(&path).unwrap_or_else(|error| panic!("{path}: {error}"));
    let value =
        amphora_core::parse_json_strict(&bytes).unwrap_or_else(|error| panic!("{path}: {error}"));
    let selected = pointer
        .as_deref()
        .map(|pointer| {
            value
                .pointer(pointer)
                .unwrap_or_else(|| panic!("JSON pointer is absent: {pointer}"))
        })
        .unwrap_or(&value);
    println!("{}", amphora_core::stable_hash(selected));
}
