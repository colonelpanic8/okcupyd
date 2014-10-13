#!/bin/bash
# assuming the script is in a bin directory, one level into the repo
TOP_LEVEL="$(git rev-parse --show-toplevel)"
HOOK_DIR="$TOP_LEVEL""/.git/hooks"
SOURCE_DIR="$TOP_LEVEL""/bin/git-hooks"
echo $SOURCE_DIR

for hook in $SOURCE_DIR/*; do
    source="$SOURCE_DIR/""$(basename $hook)"
    dest="$HOOK_DIR/$(basename $hook)"
    # If the hook already exists, is executable, and is not a symlink
    if [ -e $dest ]; then
        mv $dest "$dest.local"
    fi
    echo "linking ""$source"" to ""$dest"
    ln -s  "$source" "$dest"
    chmod 755 $dest
done
