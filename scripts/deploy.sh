#!/usr/bin/env sh
set -e

npm run build

cd dist

git init
git checkout -b docs
git add -A
git commit -m 'deploy'

git push -f git@github.com:dodaydream/figure-skating-guide.git docs

cd -
rm -rf dist/.git
