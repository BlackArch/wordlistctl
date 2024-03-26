use toml::Table;

fn get_wordlist(key: &str) -> Result<toml::Value, ()> {
    if let Some(table) = toml::from_str::<Table>(include_str!("../config/repo.toml")).unwrap().get(key) {
       Ok(table.clone())
    } else {
        error!("Key not found in repo.toml");
        Err(())
    } 
}