#!/bin/bash
# assuming the script is in a bin directory, one level into the repo
TOP_LEVEL="$(git rev-parse --show-toplevel)"
HOOK_DIR="${TOP_LEVEL}""/.git/hooks"
SOURCE_DIR="$(dirname $BASH_SOURCE)""/git-hooks"

for hook in $SOURCE_DIR/*; do
    # If the hook already exists, is executable, and is not a symlink
    if [ ! -h $HOOK_DIR/$hook -a -x $HOOK_DIR/$hook ]; then
        mv $HOOK_DIR/$hook $HOOK_DIR/$hook.local
    fi
    source="$hook"
    dest="$HOOK_DIR/$(basename $hook)"
    echo "linking ""$dest""to ""$source"
    ln -s  "$hook" "$HOOK_DIR/$(basename $hook)"
done
