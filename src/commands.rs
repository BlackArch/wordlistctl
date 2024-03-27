use clap::Subcommand;

use crate::args;

#[derive(Subcommand, Debug)]
pub(crate) enum Command {
    Fetch(args::FetchArgs),
    Search(args::SearchArgs),
}
