## Description

Script to fetch, install, update and search wordlist archives from websites
offering wordlists with more than 2900 wordlists available.

In the latest version of the Blackarch Linux it has been added to
**/usr/share/wordlists/** directory.

## Installation

`pacman -S wordlistctl`

## Usage

```
[ sepehrdad@blackarch-dev ~/blackarch/repos/wordlistctl ]$ wordlistctl -H
--==[ wordlistctl by blackarch.org ]==--

usage:

  wordlistctl -f <arg> [options] | -s <arg> [options] | -S <arg> | <misc>

options:

  -f <num>   - download chosen wordlist - ? to list wordlists with id
  -d <dir>   - wordlists base directory (default: /usr/share/wordlists)
  -c <num>   - change wordlists category - ? to list wordlists categories
  -s <regex> - wordlist to search using <regex> in base directory
  -S <regex> - wordlist to search using <regex> in sites
  -h         - prefer http
  -X         - decompress wordlist
  -F <str>   - list wordlists in categories given
  -r         - remove compressed file after decompression
  -t <num>   - max parallel downloads (default: 5)

misc:

  -C         - disable terminal colors
  -T         - disable torrent download
  -P         - set proxy (format: proto://user:pass@host:port)
  -A         - set useragent string
  -Y         - proxy http
  -Z         - proxy torrent
  -M         - use multiprocessing for parallelization
  -N         - do not ask for any confirmation
  -I         - do not check for integrity
  -V         - print version of wordlistctl and exit
  -H         - print this help and exit

example:

  # download and decompress all wordlists and remove archive
  $ wordlistctl -f 0 -Xr

  # download all wordlists in username category
  $ wordlistctl -f 0 -c 0

  # list all wordlists in password category with id
  $ wordlistctl -f ? -c 1

  # download and decompress all wordlists in misc category
  $ wordlistctl -f 0 -c 4 -X

  # download all wordlists in filename category using 20 threads
  $ wordlistctl -c 3 -f 0 -t 20

  # download wordlist with id 2 to "~/wordlists" directory using http
  $ wordlistctl -f 2 -d ~/wordlists -h

  # print wordlists in username and password categories
  $ wordlistctl -F username,password

  # download all wordlists with using tor socks5 proxy
  $ wordlistctl -f 0 -P "socks5://127.0.0.1:9050" -Y

  # download all wordlists with using http proxy and noleak useragent
  $ wordlistctl -f 0 -P "http://127.0.0.1:9060" -Y -A "noleak"

note:

  * Wordlist's id are relative to the category that is chosen
  * and are not global, so by changing the category Wordlist's
  * id changes.

```

## Get Involved

You can get in touch with the BlackArch Linux team. Just check out the following:

**Please, send us pull requests!**

**Web:** https://www.blackarch.org/

**Mail:** team@blackarch.org

**IRC:** [irc://irc.freenode.net/blackarch](irc://irc.freenode.net/blackarch)
