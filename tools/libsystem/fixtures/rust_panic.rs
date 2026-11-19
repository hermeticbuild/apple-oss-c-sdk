fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    let panic = std::panic::catch_unwind(|| panic!("caught Darwin panic"));
    assert!(panic.is_err());
}
