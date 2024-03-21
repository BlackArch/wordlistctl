pub mod units {
    // https://gist.github.com/rust-play/303fb1b404e27c3549c6380884bbb5ac

    pub enum Units {
        Byte,
        Mb,
        Kb,
        Gb,
        Tb
    }

    impl std::fmt::Display for Units {
        fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
            match self {
                Units::Byte => write!(f, "bytes"),
                Units::Mb => write!(f, "MB"),
                Units::Kb => write!(f, "KB"),
                Units::Gb => write!(f, "GB"),
                Units::Tb => write!(f, "TB"),
                _ => panic!("unknown size"),
            }
        }
    }

    #[allow(dead_code)]
    pub fn readable_size(size: &mut f32) -> String {
        let mut counter: u8 = 0;
        while *size > 1000.00 {
            *size /= 1000.00;
            counter += 1;
        }
        let unit: Units = match counter {
            0 => Units::Byte,
            1 => Units::Mb,
            2 => Units::Kb,
            3 => Units::Gb,
            4 => Units::Tb,
            _ => panic!("Unknown size")
        };

        format!("{size:.2} {unit}").to_string()
    }
}
