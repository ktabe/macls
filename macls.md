# macls.py reference

Full option and color reference for `macls.py`. For an overview of what it
does and why, see [README.md](README.md).

## Synopsis

```
macls.py [-I] [--scale=n] [--ql-ext=spec] [-B] [--color=when] [--theme=mode] [--tag-colors=mode]
          [--columns=mode] [--tag=mode] [--stripe] [--suffix-color=mode]
          [--fg-mode=mode] [--base-fg=RRGGBB] [--quote]
          [--group-directories-first]
          [-a] [-A] [-l] [-h] [-1] [-C] [-F] [-t] [-S] [-X] [-r] [-d]
          [-R] [--help] [--version] [path ...]
```

## Description

macls.py is an alternative implementation of the `ls` command for macOS,
designed as a drop-in replacement for the standard `ls` with colorized
output and image thumbnails added on top.

Unlike the standard `ls`, which uses a fixed color scheme based on file
type, macls.py uses a dynamic color scheme that reflects the recency of
file modifications and Finder tags: a name's foreground color is a
gradient based on how recently it was modified, and its background color
is based on Finder tagging (`_kMDItemUserTags`).

With no options, and standard output attached to a terminal, entries are
listed in `ls`'s default `-C` (multi-column, down-then-across) layout.

When standard output is a terminal, each entry's name is wrapped in an
OSC 8 hyperlink pointing at its `file://` URL. Terminals that support OSC 8
(including iTerm2) let the name be clicked to open it; terminals without
OSC 8 support just show the name as plain text. In iTerm2 specifically,
Cmd-click on a name reveals/opens it in Finder via Semantic History.

If an option macls.py doesn't recognize is passed, it falls back to the
standard `/bin/ls`.

Like GNU `ls` (and unlike the standard macOS `ls`), options and path
arguments may be freely mixed in any order — `macls.py file.txt -l` works
the same as `macls.py -l file.txt`. A literal `--` stops option parsing
outright; everything after it, even something that looks like an option,
is taken as a path argument.

## Options

### macls.py extensions

These options have no equivalent in the standard macOS `ls(1)`.

**`-I`**
Display a thumbnail of image files, and of Word/Excel/PowerPoint
documents (modern `.docx`/`.xlsx`/`.pptx` or legacy `.doc`/`.xls`/`.ppt`
— an actual rendered first-page/sheet/slide preview via macOS's Quick
Look, not a generic icon), to the left of the name, using
iTerm2's inline image protocol (OSC 1337). Ignored outside iTerm2, or
when standard output is not a terminal. The thumbnail's width is fixed
(see `--scale`); for PNG/GIF/BMP/JPEG, its height is instead computed
from that image's own aspect ratio, so a landscape photo doesn't end up
with wasted blank space around it. Every other image extension keeps a
flat height. Either way, the height actually used is capped to the
terminal's own height, since a thumbnail taller than the terminal would
corrupt the image and misplace whatever's printed after it.

**`--scale=n`**
Multiplies the `-I` thumbnail's width by `n` (a positive integer) — and
its height too, for any image extension whose height isn't computed from
the image's own aspect ratio. Has an effect only in `-1` or `-l`, the two
single-line-per-entry contexts `-I` is active in to begin with; ignored
in multi-column output, where several entries share one physical line.

If the thumbnail plus the entry's own text would together overflow the
terminal's width, that entry's layout switches from side-by-side to
stacked: the text prints on its own line, then the thumbnail prints below
it — other entries whose text is short enough stay side by side. `n`
itself is only reduced (silently) when the thumbnail alone would be
wider than the terminal.

Omitting `--scale` is equivalent to `--scale=1` (the base size, one row
tall). Has no effect without `-I`.

**`--ql-ext=spec`**
Adjusts which extensions `-I` tries a Quick Look preview for (see `-I`
above), beyond image files, which are unaffected either way. `spec` is
one of:

| `spec` | Behavior |
|---|---|
| `off` | Disables Quick Look thumbnails entirely. |
| `all` | Every extension not already an image file becomes a Quick Look candidate, not just the default Word/Excel/PowerPoint list (extension-less files are still skipped) — can be noticeably slower over a directory with many non-image files. |
| `ext,ext,...` | A comma-separated list of extensions (with or without a leading dot, e.g. `md,rtf`) added on top of the default list, not replacing it. |

Has no effect without `-I`. A value is always required (unlike
`--scale`/`--tag`/etc., there's no bare `--ql-ext` form).

**`-B`**
Show directory names in bold.

**`--color=when`**
Controls when output is colorized.

| `when` | Behavior |
|---|---|
| `always` | Always colorize output. |
| `auto` (default) | Colorize output only when standard output is a terminal. |
| `never` | Never colorize output. |

Omitting `when` (bare `--color`) is equivalent to `--color=always`.

**`--theme=mode`**
Selects which color gradient (see [Colors](#colors) below) to use for the
terminal's background.

| `mode` | Behavior |
|---|---|
| `light` | Use the gradient designed for a light terminal background. |
| `dark` | Use the gradient designed for a dark terminal background. |
| `auto` (default) | Detect the background from the `COLORFGBG` environment variable (set by iTerm2 and several other terminals); falls back to `light` if it isn't set or can't be parsed. |

Omitting `mode` (bare `--theme`) is equivalent to `--theme=auto`.

**`--tag-colors=mode`**
Selects the Finder tag color palette (see [Colors](#colors) below), used
only when the terminal supports 24-bit truecolor.

| `mode` | Behavior |
|---|---|
| `vivid` | Saturated colors matching the Finder tag hues. |
| `pastel` (default) | Softer, desaturated colors. |

Omitting `mode` (bare `--tag-colors`) is equivalent to `--tag-colors=pastel`.

**`--columns=mode`**
Selects the multi-column layout mode.

| `mode` | Behavior |
|---|---|
| `compact` (default) | Column width is normally based on the longest name across every entry, same as `classic`. But an entry unusually longer than the "typical" entries spans multiple column slots on its own row instead of widening every column; the following column(s) simply skip that row. If this doesn't actually fit more columns than `classic` would, `classic` is used instead. |
| `classic` | Always behaves like plain `ls -C`: column width is fixed at the longest name across every entry, so a single very long name can widen every column. |

Omitting `mode` (bare `--columns`) is equivalent to `--columns=compact`.

**`--tag=mode`**
Selects how Finder tags (see [Colors](#colors) below) are shown for each
entry.

| `mode` | Behavior |
|---|---|
| `bg` (default) | Uses the color of the entry's last Finder tag, if any, as the entry's background. If there are multiple tags, the colors of the others are appended after the name as tightly packed dots (●), ordered from the second-to-last tag back to the first. |
| `dot` | Never sets a background color from a Finder tag; every tag (not just the extras) shows as a dot after the name instead, ordered from the last tag back to the first. |
| `str` | Appends every Finder tag's name after the entry, in assignment order, as a bracketed comma-separated list (e.g. `report.pdf [Work, Urgent]`). A tag with a color is shown in that color; a tag with no color assigned is shown in the terminal's default foreground color. Never sets a background color from a tag. With `--stripe`, the whole label — brackets and commas included — picks up the entry's striped-column tint. |
| `off` | Never shows a Finder tag in any form. |

Omitting `mode` (bare `--tag`) is equivalent to `--tag=bg`.

**`--stripe`**
Tints every entry's background, filling the entry's full column width,
alternating between two tints by column (even columns get one tint, odd
columns the other), so adjacent columns read as distinct bands. In
`--columns=compact` mode, an entry that spans multiple columns stripes
according to the column it starts in.

With `--tag=bg` (the default), an entry with a Finder tag keeps that
tag's own color for the name itself; only the rest of the column gets
the stripe tint. An entry with no tag gets the stripe tint across the
whole column. With `--tag=dot`, `--tag=str`, or `--tag=off`, every column
always gets the stripe tint regardless of whether the entry has a tag.

In `-l`, there's no column, so the entry's row (odd rows) takes the place
of a column: the whole line gets the tint (`--tag=bg` still wins for the
name itself). Only odd rows are tinted; even rows are left with no
background.

In `-1`, and in plain non-tty output without `-C`, the entry's row
likewise stands in for a column, but only the name itself is tinted on
odd rows, since there's no permissions/owner/size/date text surrounding
it. Multi-column output forced there by `-C` stripes by column as usual.

**`--suffix-color=mode`**
Selects the color of the `-F` type indicator (`/ @ * = |`) appended to
an entry.

| `mode` | Behavior |
|---|---|
| `off` (default) | The indicator takes on the same color as the entry's name (foreground gradient, and any Finder tag or stripe background), i.e. no color of its own. |
| `type` | The indicator gets its own foreground color keyed by which character it is, matching `/bin/ls -G`'s default `LSCOLORS` for that file type: `/` (directory) blue, `@` (symlink) magenta, `=` (socket) green, `\|` (pipe) yellow, `*` (executable) red. Always the plain ANSI 8-color codes, regardless of `--color`/`--tag-colors` or light/dark background. |

Omitting `mode` (bare `--suffix-color`) is equivalent to
`--suffix-color=off`. Has no effect without `-F`.

**`--fg-mode=mode`**
Selects whether a name's own foreground color is set from its recency
gradient.

| `mode` | Behavior |
|---|---|
| `date` (default) | Colors each name by how recently it was modified (see [Colors](#colors) below). |
| `off` | Leaves names in the terminal's default foreground color. Finder tag and stripe backgrounds are unaffected either way. |

Omitting `mode` (bare `--fg-mode`) is equivalent to `--fg-mode=date`.

**`--base-fg=RRGGBB`**
Overrides the color the oldest files (beyond the 1-month threshold, see
[Colors](#colors) below) fade to in the recency gradient, as a 6-hex-digit
RGB value (e.g. `808080` for gray). Without `--base-fg`, that endpoint is
a fixed guess ((0,0,0) black for a light background, light gray for a
dark one) at the terminal's own default text color; `--base-fg` lets it
be stated directly instead, since actual terminal foreground colors vary
widely between users/themes. The whole gradient is then a straight
linear interpolation from the starting color to `RRGGBB`. Has no effect
with `--fg-mode=off`.

**`--quote`**
Wraps a displayed name in shell quotes whenever it contains whitespace, a
shell metacharacter (`` ` $ & ; | ( ) < > * ? [ ] { } ! " ' \ ``), or a
leading `~` or `#` (both only significant as the first character of a
word), so it's safe to paste directly into a shell command line. Names
with none of those are left unquoted. Normally single-quoted; if the name
itself contains a `'`, double quotes are used instead (escaping
`` $ ` " \ `` inside), matching GNU ls's `--quoting-style=shell`. With
`-F`, the type indicator is appended after the closing quote, not inside
it.

If any name in the listing needs quoting, every unquoted name gets a
leading space in its place, so the opening quote of a quoted name hangs
one column to the left of its unquoted neighbors' text rather than
pushing that text out of alignment. Applies in both `-C` and `-l`.

A name containing a control character (e.g. the CR in `Icon\r`, the
marker for a Finder folder custom icon) is normally displayed with each
such character replaced by `?`, which loses the original bytes.
`--quote` instead uses ANSI-C quoting (`$'...'`, bash/zsh syntax, e.g.
`$'Icon\r'`), with each such character backslash-escaped, so the
displayed name pastes back into a shell as the exact original name.

**`-X`**
Sort by extension: the text after the last `.` in each name (no
extension sorts first), ties broken by whatever order was otherwise in
effect. This is a GNU ls `-X`, not a macOS one — macOS's own `/bin/ls -X`
means "don't descend into directories that cross filesystem boundaries"
during a recursive listing, a completely unrelated flag.

**`--group-directories-first`**
Lists directories before every other entry, stable-sorting them to the
front so whatever order `-t`/`-S`/`-X`/`-r` (or plain name order) already
produced is preserved within each group. Directory-ness is checked by
following symlinks (a symlink to a directory is grouped as one, matching
GNU ls's own `--group-directories-first`), unlike `-F`/`-B`'s own
lstat-based classification, which shows a symlink to a directory as a
symlink, not a directory.

### Standard ls(1) options

These mirror the standard macOS `ls(1)`.

| Option | Behavior |
|---|---|
| `-a` | Show all files, including `.` and `..` |
| `-A` | Show all files except `.` and `..` |
| `-l` | Use long format (permissions, owner, size, date, etc.) |
| `-h` | With `-l`, show file sizes in human-readable form (e.g. `1.0K`, `234M`, `2.3G`). Has no effect without `-l`. |
| `-1` | Force single-column, one-entry-per-line output |
| `-C` | Force multi-column output, even when standard output isn't a terminal |
| `-F` | Append a type indicator (one of `/ @ * = \|`) to entries (see `--suffix-color` for its color) |
| `-t` | Sort by modification time, newest first |
| `-S` | Sort by file size, largest first |
| `-r` | Reverse whatever sort order is otherwise in effect |
| `-d` | List directories themselves, not their contents |
| `-R` | Recursively list subdirectories encountered |
| `--help` | Print a usage message and exit |
| `--version` | Print the version number and exit |

`-1`, `-C`, and `-l` select mutually exclusive display formats; when more
than one is given, whichever comes last on the command line wins
(matching real `ls`'s own handling of its format options).

When standard output is a pipe or a file, coloring is disabled by default
(set the `CLICOLOR_FORCE` environment variable to force it regardless);
`--color` overrides both of these.

## Colors

### Foreground

An 8-step gradient based on how recently the file was modified (disabled
by `--fg-mode=off`, which leaves names in the terminal's default
foreground color instead). The steps are determined by fixed elapsed-time
thresholds: 5 min / 30 min / 1 hour / 2 hours / 1 day / 1 week / 1 month /
beyond.

Two color families are provided and switched based on the background
color, so foreground and background don't clash in hue:

- **cyan family** — starts at vivid cyan. Used when the background is
  anything other than green/blue (gray, purple, yellow, red, orange).
- **magenta family** — starts at vivid magenta. Used when the background
  is green/blue, and as the default when there is no background (no
  Finder tag).

Each family additionally has a light-background and a dark-background
variant (`--theme`): the light-background stops sink toward black as
files age; the dark-background stops instead desaturate toward a light
gray, since fading to black would make old files invisible against a
dark background. `--base-fg` overrides that endpoint directly, for
terminals whose own default foreground color isn't well approximated by
either guess.

### Background

With `--tag=bg` (the default), if one or more Finder tags are present,
the color of the last tag in `_kMDItemUserTags` (in the order the tags
were assigned) is used as the background. When there are multiple tags,
the colors of the other tags are appended after the name as tightly
packed dots (●), ordered from the second-to-last tag back to the first.
With `--tag=dot`, every tag is a dot instead, ordered from the last tag
back to the first, and no background color is set from a Finder tag at
all; `--tag=str` likewise never sets a background, and `--tag=off` shows
no tag information at all. If there are no tags, no background color is
set either way.

Finder tag colors used as a background:

| Tag color | ANSI 256 |
|---|---:|
| Gray | 244 |
| Green | 2 |
| Purple | 5 |
| Blue | 33 |
| Yellow | 3 |
| Red | 1 |
| Orange | 208 |

In 24-bit truecolor mode, the Finder tag color comes from a palette
selected by `--tag-colors` (`vivid`/`pastel`); in ANSI 256-color mode,
`--tag-colors` has no effect.

With `--stripe`, entries that end up with no Finder tag background
instead get a subtle gray tint alternated by the entry's starting column
in the multi-column grid; with `--tag=dot`, `--tag=str`, or `--tag=off`,
every entry gets that same tint unconditionally, since no Finder tag is
ever used as the background then.

## Notes

- Enumerating/sorting directory contents and the `-l` long-format output
  (permission bits, owner/group, size alignment, date formatting, etc.)
  is delegated to the system `ls(1)`, to match its behavior exactly.
- Finder tags are read directly from the `com.apple.metadata:_kMDItemUserTags`
  extended attribute — macOS-only. On other platforms, files are always
  treated as untagged.
- `-I` thumbnails only render in iTerm2, with standard output attached to
  a terminal.
- Thumbnail height can only be computed from the image's own aspect ratio
  for PNG/GIF/BMP/JPEG; other image extensions keep a flat height.
