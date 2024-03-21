mod units {
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
                Units::Byte => write!("bytes"),
                Units::Mb => write!("mb"),
                Units::Kb => write!("kb"),
                Units::Gb => write!("gb"),
                Units::Tb => write!("tb"),
                _ => panic!("unknown size"),
            }
        }
    }

    pub fn readable_size(size: &mut f32) -> &str {
        use Units;
        let mut counter: u8 = 0;
        while size > 1000 {
            size /= 1000;
            i++;
        }
        let unit: Units = match counter {
            0 => Byte,
            1 => Mb,
            2 => Kb,
            3 => Gb,
            4 => Tb,
            _ => panic!("Unknown size")
        };

        format!("{size:.2} {unit}")
    }
}