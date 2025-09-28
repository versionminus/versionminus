#! /bin/bash
# Enable bash completion
if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
fi

# cli autocompletions
if [ -f /etc/bash_completion.d/git ]; then
    source /etc/bash_completion.d/git
fi

if [ -f /etc/bash_completion.d/docker ]; then
    source /etc/bash_completion.d/docker
fi

# Docker Build Optimisation
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Function to get repository name from git remote
get_repo_name() {
    local repo_url
    repo_url=$(git remote get-url origin 2>/dev/null)

    # Handle various remote URL formats
    if [[ $repo_url =~ github\.com[:/]([^/]+)/([^/.]+) ]]; then
        # Standard GitHub: https://github.com/user/repo or git@github.com:user/repo
        echo "${BASH_REMATCH[2]}"
    elif [[ $repo_url =~ :([^/]+)/([^/.]+)\.git$ ]]; then
        # SSH format: nngithub:user/repo.git
        echo "${BASH_REMATCH[2]}"
    elif [[ $repo_url =~ :([^/]+)/([^/.]+)$ ]]; then
        # SSH format without .git: nngithub:user/repo
        echo "${BASH_REMATCH[2]}"
    elif [[ $repo_url =~ /([^/.]+)\.git$ ]]; then
        # Any URL ending with /repo.git
        echo "${BASH_REMATCH[1]}"
    elif [[ $repo_url =~ /([^/]+)$ ]]; then
        # Any URL ending with /repo
        echo "${BASH_REMATCH[1]}"
    else
        # Fallback to current directory name
        echo "$(basename "$(pwd)")"
    fi
}

# Dark GitHub themed PS1 with cool icons
# Colors (dark theme)
RESET='\[\033[0m\]'
BOLD='\[\033[1m\]'
WHITE='\[\033[97m\]'
GRAY='\[\033[90m\]'
BLUE='\[\033[94m\]'
GREEN='\[\033[92m\]'
ORANGE='\[\033[93m\]'

# Cool minimal icons
ARROW_ICON="❯"

# Set the PS1 with dynamic repository name and current directory
PS1="${GRAY} ${WHITE}${BOLD}$(whoami)${RESET}${GRAY}@${PURPLE}${BOLD}\$(get_repo_name)${RESET} ${BLUE}${GREEN}\w${RESET}\n ${ORANGE}${BOLD}${ARROW_ICON}${RESET} "

# git utils
alias gc='git commit -m' # gc "feat: <message>"
alias gp='git push'
alias gpl='git pull'
alias gst='git status'
alias gco='git checkout' # gco <branch-name>
alias gcb='git checkout -b' # gcb <new-branch-name>
alias gl='git log --oneline --graph --decorate --all'
alias ga='git add' # ga <file-name>
alias gaa='git add .'
