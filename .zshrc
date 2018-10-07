# Lines configured by zsh-newuser-install
HISTFILE=~/.histfile
HISTSIZE=1000
SAVEHIST=1000
bindkey -e
# End of lines configured by zsh-newuser-install

POWERLEVEL9K_CARRIAGE_RETURN_ICON=" "
POWERLEVEL9K_OK_ICON=" "
POWERLEVEL9K_MODE="nerdfont-complete"
POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(status history)
ZSH_THEME="powerlevel9k/powerlevel9k"
export DEFAULT_USER="$(whoami)"

source $ZSH/oh-my-zsh.sh
