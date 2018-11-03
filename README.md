## Description

Script to fetch, install, update and search wordlist archives from websites
offering wordlists.

In the latest version of the Blackarch Linux it has been added to
**/usr/share/wordlists/** directory.

## Installation

`pacman -S wordlistctl`

## Usage

```
[ noptrix@blackarch-dev ~/blackarch/repos/sploitctl ]$ ./wordlistctl -h
--==[ wordlistctl.py by blackarch.org ]==--

usage:
  wordlistctl.py -f <num>  [options] | -s <arg> | <misc>

options:

  -f <num>   - download chosen wordlist
             - ? to list wordlists
             - h to show options
  -d <dir>   - wordlists base directory (default: /usr/share/wordlists)
  -s <regex> - wordlist to search using <regex> in base directory

misc:

  -U         - update config files
  -v         - print version of wordlistctl and exit
  -h         - print this help and exit


```

## Get Involved

You can get in touch with the BlackArch Linux team. Just check out the following:

**Please, send us pull requests!**

**Web:** https://www.blackarch.org/

**Mail:** team@blackarch.org

**IRC:** [irc://irc.freenode.net/blackarch](irc://irc.freenode.net/blackarch)
