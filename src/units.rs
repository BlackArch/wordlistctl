// https://gist.github.com/rust-play/303fb1b404e27c3549c6380884bbb5ac

#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum Units {
    Byte,
    Mb,
    Kb,
    Gb,
    Tb,
}

impl std::fmt::Display for Units {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Units::Byte => write!(f, "bytes"),
            Units::Mb => write!(f, "MB"),
            Units::Kb => write!(f, "KB"),
            Units::Gb => write!(f, "GB"),
            Units::Tb => write!(f, "TB"),
            _ => Err(std::fmt::Error),
        }
    }
}

pub fn get_unit(unit: &str) -> Units {
    match unit {
        "bytes" => Units::Byte,
        "mb" => Units::Mb,
        "kb" => Units::Kb,
        "gb" => Units::Gb,
        "tb" => Units::Tb,
        _ => panic!("Unknown unit"),
    }
}

#[allow(dead_code)]
pub fn readable_size(size: usize) -> (f64, Units) {
    let mut counter: u8 = 0;
    let mut size: f64 = size as f64;
    while size > 1000.00 {
        size /= 1000.00;
        counter += 1;
    }
    let unit: Units = match counter {
        0 => Units::Byte,
        1 => Units::Mb,
        2 => Units::Kb,
        3 => Units::Gb,
        4 => Units::Tb,
        _ => panic!("Unknown size"),
    };

    (size, unit)
}
