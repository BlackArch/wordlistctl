use clap::{
    crate_authors, crate_description, crate_version, value_parser, Arg, ArgAction, ArgGroup,
    Command,
};

use toml;

#[macro_use]
extern crate log;

mod data;
mod repo;
mod units;

fn main() {
    pretty_env_logger::init();

    #[allow(unused_variables)]
    let cli = Command::new("rwordlistctl")
        .author(crate_authors!())
        .version(crate_version!())
        .about(crate_description!())
        .subcommand(
            Command::new("fetch")
                .about("Fetch wordlists")
                .args(&[
                    Arg::new("decompress")
                        .short('d')
                        .long("decompress")
                        .action(ArgAction::SetTrue)
                        .help("Decompress and remove the archive file"),
                    Arg::new("workers")
                        .short('w')
                        .long("workers")
                        .value_name("COUNT")
                        .help("Number of download workers")
                        .num_args(1)
                        .require_equals(true)
                        .allow_negative_numbers(false)
                        .value_parser(value_parser!(u8).range(1..=100)),
                        // .default_value(get_workers().as_str()),
                    Arg::new("user-agent")
                        .short('u')
                        .long("user-agent")
                        .value_name("USER_AGENT")
                        .help("User agent to use for fetching")
                        .num_args(1)
                        .require_equals(true)
                        .default_value("rwordlistctl/0.1.0"),
                    Arg::new("base-dir")
                        .short('b')
                        .long("base-dir")
                        .value_name("DIR")
                        .help("Base directory to store wordlists")
                        .num_args(1)
                        .require_equals(true),
                    Arg::new("wordlist")
                        .short('l')
                        .long("wordlist")
                        .value_name("WORDLIST")
                        .help("Wordlist to fetch")
                        .num_args(1..)
                        .require_equals(true)
                        .value_delimiter(','),
                ])
                   // args to do
                   // -g --group  num_args=1 or more choices=[usernames, passwords, discovery, fuzzing, misc]
                   // fetch-term `SEE WORDLISTCTL.PY`
        )
        .group(ArgGroup::new("fetch").args([
            "decompress",
            "workers",
            "user-agent",
            "base-dir",
            "wordlist",
            "group",
        ]))
        .get_matches();
}
