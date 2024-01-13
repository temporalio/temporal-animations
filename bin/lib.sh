fzf() {
    command fzf --layout reverse --exact --cycle --height 50% --info hidden --prompt ' ' --border rounded --color light
}

list-scenes() {
    ls scenes/*.py | sed -E 's,scenes/(.+)\.py,\1,'
}
