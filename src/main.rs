use clap::{
    arg, crate_authors, crate_description, crate_version, value_parser, Arg, ArgAction, ArgGroup, Command
};

mod units;


fn main() {
    #[allow(unused_variables)]
    let cli = Command::new("rwordlistctl")
        .author(crate_authors!())
        .version(crate_version!())
        .about(crate_description!())
        .subcommand(
            Command::new("fetch")
                .about("Fetch wordlists")
                .arg(
                    Arg::new("decompress")
                        .short('d')
                        .long("decompress")
                        .help("Decompress and remove the archive file")
                        .action(ArgAction::SetTrue)
                )
                .arg( // implement validator later
                    arg!(-w --workers [COUNT] "Number of download workers")
                        .value_parser(value_parser!(u8).range(1..=100))
                        .allow_negative_numbers(false)
                        .require_equals(true)
                )
                // args to do
                // -d --decompress store_true
                // -w --workers type=int default=10
                // -u --user-agent 
                // -b --base-dir 
                // -l --wordlist num_args=1 or more
                // -g --group  num_args=1 or more choices=[usernames, passwords, discovery, fuzzing, misc]
                // fetch-term `SEE WORDLISTCTL.PY`
        )
        .group(ArgGroup::new("fetch")
            .args(["decompress", "workers", "user-agent", "base-dir", "wordlist", "group"])
        )
        .get_matches();
}