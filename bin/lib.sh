fzf() {
    command fzf --layout reverse --exact --cycle --height 50% --info hidden --prompt ' ' --border rounded --color light
}

fzf-scene() {
    ls scenes/*.py | grep -v scenes/scene\.py | fzf
}
