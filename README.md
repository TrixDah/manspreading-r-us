# Mentone Manspreaders

Static site built with Jekyll and hosted on GitHub Pages. Stories live in `_articles/`
as Markdown files and are edited through Pages CMS (https://pagescms.org).

## Publishing a story (no code)
1. Sign in at pagescms.org with GitHub and open this repo.
2. Articles -> Add an entry. Fill in the fields, write the story, Save.
3. The site updates about a minute later.

Front page position: set a story to **Lead** or **Side** to feature it. The newest story
set to each position is shown; the rest appear under Latest Stories automatically.

## Publishing a story (by hand)
Copy any file in `_articles/`, change the front matter and text, commit and push.

## Preview locally (optional)
    bundle install
    bundle exec jekyll serve
