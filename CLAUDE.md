# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`macls.py` is a single-file, dependency-free Python 3 script that's a drop-in
colorized replacement for macOS's `ls`. There is no package layout, build
step, or test suite — everything lives in `macls.py`. `README.md` (English)
and `README-ja.md` (Japanese) are the feature-overview/screenshots docs;
`macls.md` is the full option and color reference for end users; the module
docstring at the top of `macls.py` is the authoritative source those two are
kept in sync with (man-page style, every option and color rule).

## Commands

- Syntax/compile check (closest thing to a build step): `python3 -m py_compile macls.py`
- Run it directly: `./macls.py [options] [path...]` (or `python3 macls.py ...`)
- There is no automated test suite. `test/` is a fixture directory of
  oddly-named files (leading `~`/`#`, embedded `'`, shell metacharacters,
  spaces) used for manually exercising `--quote`/quoting behavior — inspect
  by running macls.py against it, e.g. `./macls.py --quote -1 test/`.
- To verify a change manually, create files/dirs with `touch`/`mkdir`, and to
  test Finder tag behavior, write the `com.apple.metadata:_kMDItemUserTags`
  xattr directly via Python's `plistlib`/`xattr` command (see any recent
  commit's testing for the pattern) rather than relying on Finder UI.

## Architecture

Everything is in `macls.py`, organized top-to-bottom as:

1. **Constants/tables** — Finder tag color palettes (ANSI 256 and 24-bit
   truecolor, vivid/pastel), the recency→color gradient stops
   (`DATE_COLOR_STOPS_*`), stripe tint tables, suffix-type colors.
2. **Pure helper functions** — color math (`rgb_to_ansi256`, `date_color_rgb`,
   `finder_sgr`, `stripe_sgr`), Finder tag retrieval (`get_finder_tags`/
   `get_finder_tag_nums`, via `ctypes` calling libc's `getxattr(2)` directly —
   macOS's Python lacks `os.getxattr`), display-width/quoting helpers
   (`display_width`, `sanitize_display_name`, `shell_quote`, `ansi_c_quote`).
3. **`Options` dataclass** — one flag/field per CLI option; `parse_options()`
   fills it in from `argv`.
4. **Per-entry builders** — `_build_entries()` computes each entry's
   pre-color display metadata (quoted name, suffix, Finder tag/dot info, the
   `--tag` name label) and its display width, *before* the multi-column
   layout is computed (needed because `--bg-mode=stripe` has to know each
   entry's starting column). `_build_final_entries()` then turns that into
   the actual colored/hyperlinked strings via `build_colored_name()`.
5. **Layout** — `compute_multi_column_layout()` computes a down-then-across
   grid purely from entry widths (`classic` = fixed column width like real
   `ls -C`; `compact`, the default, lets outlier-long names span multiple
   column slots instead of stretching every column). `render_multi_column_layout()`
   turns that layout + the colored strings into output lines, including
   `--bg-mode=stripe`/`finder-stripe` column/row tinting.
6. **`-l` handling** — `_render_long_format()` shells out to real `ls -l` for
   permissions/owner/size/date (deliberately not reimplemented — see the
   module docstring's IMPLEMENTATION NOTES) and splices the colored name
   back into each line via `splice_colored_name()`, matching lines back up
   by `order` when `--group-directories-first`/`-X` reordered entries.
7. **`list_target()`** — orchestrates one directory/file-group section: runs
   `ls -1`/`ls -l`, applies Python-side sorting (`-X`,
   `--group-directories-first` — both need to happen in Python; see
   `_build_ls_flags()`'s docstring for why `-X` can't be passed through to
   macOS's `ls`), then calls the builders/layout above and handles `-R`
   recursion.
8. **CLI entry** — `parse_options()`/`main()`. Any option macls.py doesn't
   recognize falls back to real `ls` via `os.execvpe` (see
   `plain_ls_fallback_argv_env()`), preserving the fallback's own color
   decision.

### Key invariants to preserve when adding an option

- **Update all the places an option is documented**: the module docstring
  (top of file, man-page style — SYNOPSIS line, DESCRIPTION entry, and
  COLORS/IMPLEMENTATION NOTES if relevant), `print_help()`, and `macls.md`
  (the full option/color reference, trimmed of internal implementation
  detail the docstring carries). These have drifted out of sync before —
  check `macls.md` isn't stale relative to the docstring when touching
  options. Both are intentionally kept, not consolidated into just
  `macls.md`: the docstring travels with `macls.py` itself (readable via
  `pydoc`/`help()`/opening the file) even when the script is copied out of
  this repo on its own, which matters since it's meant to be a
  dependency-free, drop-in single file.
- **Color output must respect `opts.use_color`** — any code path that emits
  SGR escape sequences based on a mode flag (e.g. `--bg-mode=stripe`'s column
  padding) must be gated on `opts.use_color`, not just on the mode value
  itself, or piping to a non-terminal without `--color=always`/`CLICOLOR_FORCE`
  leaks escape codes into the output.
- **Width accounting**: anything appended to a name for display (suffix,
  Finder-tag dots via `dot_extra_width()`, the `--tag` label via
  `build_tag_label()`) must be added to `disp_len`/`namelen`/`plainlen` in
  `_build_entries()`, or multi-column alignment breaks.
- **Unsupported-option fallback**: a new boolean long option needs adding to
  `MACLS_ONLY_LONG_OPTS` (or `MODE_OPTIONS` for a `--foo=value` style one) so
  `strip_macls_only_options()` knows to strip it before falling back to real
  `ls` for a command line mixing supported and unsupported options.
- **`-l` splicing**: extra per-entry text (like `--tag`'s label) should be
  appended to the string handed to `_render_long_format()`/`final[]` rather
  than baked into the name used for matching against real `ls -l` output,
  since `splice_colored_name()` matches on the original name.
