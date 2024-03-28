use clap::{value_parser, ArgAction, Args};

#[derive(Args, Debug)]
pub struct FetchArgs {
    #[arg(
        short = 'd',
        long = "decompress",
        help = "Decompress and remove the archive file", 
        action = ArgAction::SetTrue,
        default_value_t = true,
        num_args = 0,
    )]
    pub decompress: bool,

    #[arg(
        short = 'w',
        long = "workers", 
        help = "Number of download workers",
        value_name = "COUNT",
        num_args = 1,
        require_equals = true,
        allow_negative_numbers = false,
        value_parser = value_parser!(u8).range(1..=100),
        // .default_value_t()
        default_value = "5",
    )]
    pub workers: Option<u8>,

    #[arg(
        short = 'u',
        long = "user-agent",
        value_name = "USER_AGENT",
        help = "User agent to use for fetching",
        num_args = 1,
        require_equals = true,
        default_value = "rwordlistctl/0.1.0"
    )]
    pub user_agent: String,

    #[arg(
        short = 'b',
        long = "base-dir",
        value_name = "BASE_DIR",
        help = "Base directory to store wordlists",
        num_args = 1,
        require_equals = true,
        default_value = "/usr/share/wordlists"
    )]
    pub base_dir: String,

    #[arg(
        short = 'l',
        long = "wordlist",
        value_name = "WORDLISTS",
        help = "Wordlist to fetch",
        num_args(1..),
        require_equals = true,
        value_delimiter = ',',
    )]
    pub wordlists: Vec<String>,

    #[arg(
        short = 'g',
        long = "group",
        value_name = "GROUP",
        help = "Group of wordlists to fetch",
        num_args(1..=5),
        require_equals = true,
        value_delimiter = ',',
        value_parser(["usernames", "passwords", "discovery", "fuzzing", "misc"]),
    )]
    pub group: Vec<String>,
}

#[derive(Args, Debug)]
pub struct SearchArgs {
    #[arg(
        short = 'l',
        long = "local",
        help = "Search for wordlists in the local archives",
        action = ArgAction::SetTrue,
        num_args = 0,
    )]
    pub local: bool,

    #[arg(
        short = 'f',
        long = "fetch",
        help = "Fetch wordlists from the repository at the given index",
        action = ArgAction::Set,
        num_args(1..),
        require_equals = true,
        value_delimiter = ',',
        value_parser = value_parser!(u8).range(1..),
    )]
    pub fetch: u8,
}
