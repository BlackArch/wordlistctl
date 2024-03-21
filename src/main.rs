use clap::{
    crate_authors,
    crate_description,
    crate_version,
    Command,
};
use units;


fn main() {
    #[allow(unused_variables)]
    let cli = Command::new("rwordlistctl")
        .author(crate_authors!())
        .version(crate_version!())
        .about(crate_description!())
        .subcommand(
            Command::new("fetch")
                .about("Fetch wordlists")
                // TODO: FINISH FETCH
        )
        .get_matches();
}