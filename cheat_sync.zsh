#!/usr/bin/env zsh
# cheat-sync — download every cheat.sh topic into ~/.cheats for offline use
emulate -L zsh
setopt err_return no_unset pipe_fail
typeset -r cache_dir=${CHEAT_DIR:-$HOME/.cheats}
typeset -ri delay_ms=${DELAY_MS:-150}   # be gentle with cheat.sh
typeset -ri timeout=${TIMEOUT:-20}
mkdir -p -- $cache_dir
# --- 1. Fetch the master topic list -----------------------------------------
typeset -r list_file=$cache_dir/.list
print -n "Fetching topic list... "
curl -fsSL --compressed --max-time 30 https://cheat.sh/:list -o $list_file || {
  print -u2 "FAILED"; return 1
}
print "ok"
# --- 2. Normalize: unique, drop blanks and :meta entries --------------------
typeset -a topics
topics=(${(fu)${(f)"$(<$list_file)"}})
topics=(${topics:#})
topics=(${topics:#:*})       # skip ":list", ":help", ":learn", etc.
typeset -ri total=$#topics
print "Syncing $total topics → $cache_dir (delay=${delay_ms}ms)"
# --- 3. Fetch loop (resumable) ----------------------------------------------
typeset -i i=0 new=0 cached=0 failed=0
for topic in $topics; do
  (( ++i ))
  typeset safe=${topic//[^A-Za-z0-9._+-]/_}
  typeset out=$cache_dir/$safe
  if [[ -s $out ]]; then
    (( ++cached ))
  else
    typeset tmp=$cache_dir/.${safe}.$$.part
    if curl -fsSL --compressed --max-time $timeout --retry 2 \
         "https://cheat.sh/${topic// /+}" -o $tmp && [[ -s $tmp ]]; then
      mv -- $tmp $out
      (( ++new ))
    else
      rm -f -- $tmp
      (( ++failed ))
      print -u2 "FAIL: $topic"
    fi
    (( delay_ms > 0 )) && sleep $(( delay_ms / 1000.0 ))
  fi
  (( i % 100 == 0 )) && print "  [$i/$total]  new=$new cached=$cached failed=$failed"
done
print "Done: new=$new cached=$cached failed=$failed total=$total"