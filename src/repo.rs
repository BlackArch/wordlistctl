use anyhow::Context;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug)]
pub struct Repo {
    wordlists: Vec<HashMap<String, Wordlist>>,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub(crate) struct Wordlist {
    url: String,
    size: usize,
    unit: String,
    group: String,
}

#[allow(dead_code)]
fn load_repo() -> anyhow::Result<Repo> {
    let repo = toml::from_str::<Repo>(include_str!("../config/repo.toml"))
        .with_context(|| format!("Failed to read repository from repo.toml"))?;
    Ok(repo)
}

#[allow(dead_code)]
pub fn get_wordlist_by_group(group: &str) -> anyhow::Result<Vec<Wordlist>> {
    let repo: Repo = load_repo()?;
    let wordlists = repo
        .wordlists
        .into_iter()
        .filter(|wordlist| wordlist.values().next().unwrap().group == group)
        .map(|wordlist| wordlist.values().cloned().next().unwrap())
        .collect::<Vec<Wordlist>>(); // Collect the wordlists into a vector

    Ok(wordlists)
}

#[allow(dead_code)]
pub fn get_wordlist_by_name(name: &str) -> anyhow::Result<Wordlist> {
    let repo: Repo = load_repo()?;
    let wordlist = repo
        .wordlists
        .into_iter()
        .find(|wordlist| wordlist.keys().next().unwrap() == name)
        .map(|wordlist| wordlist.values().cloned().next().unwrap());
    match wordlist {
        Some(wordlist) => Ok(wordlist),
        None => anyhow::bail!("Wordlist not found"),
    }
}

// fn get_wordlist(key: &str) -> Result<toml::Value, ()> {
//     if let Some(table) = toml::from_str::<Table>(include_str!("../config/repo.toml")).unwrap().get(key) {
//        Ok(table.clone())
//     } else {
//         error!("Key not found in repo.toml");
//         Err(())
//     }
// }
