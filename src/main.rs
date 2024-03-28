use clap::Parser;

// #[macro_use]
extern crate log;

mod args;
mod commands;
mod data;
mod repo;
mod units;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None, author)]
struct  RWordlistctl {
    #[command(subcommand)]
    command: commands::Command,
}

fn main() {
    pretty_env_logger::init();

    #[allow(unused_variables)]
    let cli: RWordlistctl = RWordlistctl::parse();

    //     .group(ArgGroup::new("fetch").args([
    //         "decompress",
    //         "workers",
    //         "user-agent",
    //         "base-dir",
    //         "wordlist",
    //         "group",
    //     ]))
    //     .get_matches();
}
