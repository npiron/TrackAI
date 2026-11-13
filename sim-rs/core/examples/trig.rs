use std::io::{self, BufRead, Write};
fn main() {
    let stdin = io::stdin();
    let mut out = io::BufWriter::new(io::stdout());
    for line in stdin.lock().lines() {
        let x: f64 = f64::from_bits(u64::from_str_radix(line.unwrap().trim(), 16).unwrap());
        writeln!(out, "{:x} {:x} {:x} {:x} {:x}", x.sin().to_bits(), x.cos().to_bits(), x.tan().to_bits(), x.atan2(0.7).to_bits(), (x / 4.0).acos().to_bits()).unwrap();
    }
}
