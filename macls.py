#!/usr/bin/env python3
"""
NAME
    macls.py -- colorized directory listing for macOS

SYNOPSIS
    macls.py [-I] [--scale=n] [-B] [--color=when] [--theme=mode] [--tag-colors=mode]
               [--columns=mode] [--tag=mode] [--stripe] [--suffix-color=mode]
               [--fg-mode=mode] [--base-fg=RRGGBB] [--quote]
               [--group-directories-first]
               [-a] [-A] [-l] [-h] [-1] [-C] [-F] [-t] [-S] [-X] [-r] [-d]
               [-R] [--help] [--version] [path ...]

DESCRIPTION
    macls.py is an alternative implementation of `ls` command for
    macOS.  macls.py is implemented in Python3 and is designed to be a drop-in replacement for the standard `ls` command, with additional features for colorized output and image thumbnails.

    Unlike the standard `ls`, which uses a fixed color scheme based on file types, macls.py uses a dynamic color scheme that reflects the recency of file modifications and Finder tags.

    The foreground color of each filename is a gradient based on
    how recently the file was modified; the background color is based on
    Finder tagging (_kMDItemUserTags). If an unsupported option is
    passed, macls.py falls back to the standard `/bin/ls` command.

    With `-I` option, image files such as .jpg, .png and .pdf are displayed with a thumbnail to the left of the name, using iTerm2's inline image protocol (OSC 1337). This feature is ignored outside iTerm2 or when standard output is not a terminal.

    When standard output is a terminal, each entry's name is wrapped in an OSC 8 hyperlink escape sequence pointing at its file:// URL. Terminals that support OSC 8 (including iTerm2) let the name be clicked; in iTerm2 specifically, Cmd-click on a file:// link reveals/opens the target in Finder via Semantic History. Terminals without OSC 8 support just show the name as plain text, since they ignore the escape sequences.

    With no options and standard output attached to a terminal, entries
    are listed in ls's default -C (multi-column, down-then-across)
    layout.

    Like GNU ls (and unlike the standard macOS ls), options and path
    arguments may be freely mixed in any order -- `macls.py file.txt -l`
    works the same as `macls.py -l file.txt`. A literal `--` stops
    option parsing outright; everything after it, even something that
    looks like an option, is taken as a path argument.

    The following options are macls.py extensions with no equivalent
    in the standard macOS ls(1):

    -I          Display a thumbnail of image files (and, via macOS's
                Quick Look, Word/Excel/PowerPoint documents --
                .docx/.xlsx/.pptx and the legacy .doc/.xls/.ppt -- an
                actual rendered first-page/sheet/slide preview, not a
                generic icon) to the left of the name, using iTerm2's
                inline image protocol (OSC 1337). Ignored outside
                iTerm2, or when standard output is not a terminal. The
                thumbnail's width is fixed (see --scale); for
                PNG/GIF/BMP/JPEG (the formats whose pixel dimensions
                can be read with a small amount of standard-library-only
                header parsing -- see get_image_pixel_size()), its
                height is instead computed from that image's own real
                aspect ratio, so e.g. a landscape photo doesn't end up
                with wasted blank space around it the way a flat, fixed
                height for every thumbnail regardless of its shape
                would. Every other image extension keeps that flat
                height. Either way, the height actually used is capped
                to the terminal's own height (see get_terminal_height()):
                a thumbnail taller than the terminal forces it to
                scroll partway through drawing, which corrupts the
                image and misplaces whatever's printed after it, rather
                than just needing to be scrolled into view afterwards.

    --scale=n
                Multiplies the -I thumbnail's width by n (a positive
                integer) -- and its height too, for any image extension
                whose height isn't instead computed from the image's
                own aspect ratio (see -I above). Has an effect only in
                -1 or -l, the two single-line-per-entry contexts -I
                itself is ever active in to begin with (it's disabled
                outright on non-tty output, regardless of --scale --
                see main()); ignored (thumbnail stays at its base size,
                see ITERM_IMG_WIDTH/ITERM_IMG_HEIGHT) in multi-column
                output, where several entries' worth of text share one
                physical line and a taller thumbnail would misalign
                them. In those single-line contexts, the entry's own
                text is printed first,
                then the thumbnail is drawn over blank padding reserved
                to its left (see _build_image_prefixes()) -- so the
                name ends up top-aligned alongside a thumbnail taller
                than 1 row, rather than bottom-aligned, without needing
                any cursor-position arithmetic to place it there.

                If width*n plus an entry's own text (its name in -1, or
                the entire permissions/owner/size/date/name line in -l)
                would together overflow the terminal's width, that one
                entry's layout switches from image-then-text (sharing
                one line) to text-then-image instead: the text prints
                on its own line as usual, then the thumbnail prints
                below it on the following line(s) instead of beside it
                (see list_target()'s stacked_flags) -- entries whose
                text is short enough are unaffected and stay side by
                side. n itself is only capped (silently) in the one
                case switching to this layout can't fix on its own: the
                thumbnail alone being wider than the terminal.

                Omitting --scale is equivalent to "--scale=1" (the base
                size, one row tall, where top and bottom coincide so
                none of this applies). Has no effect without -I.

    -B          Show directory names in bold

    --color=when
                Control when output is colorized. when is one of:

                always  Always colorize output.
                auto    Colorize output only when standard output is a
                        terminal. This is the default behavior.
                never   Never colorize output.

                Omitting when (bare "--color") is equivalent to
                "--color=always".

    --theme=mode
                Selects which color gradient (see COLORS below) to use
                for the terminal's background. mode is one of:

                light   Use the gradient designed for a light terminal
                        background.
                dark    Use the gradient designed for a dark terminal
                        background.
                auto    Detect the background from the COLORFGBG
                        environment variable (set by iTerm2 and several
                        other terminals); if it isn't set or can't be
                        parsed, falls back to light. This is the
                        default behavior.

                Omitting mode (bare "--theme") is equivalent to
                "--theme=auto".

    --tag-colors=mode
                Selects the Finder tag color palette (see COLORS
                below), used only when the terminal supports 24-bit
                truecolor. mode is one of:

                vivid   Saturated colors matching the Finder tag hues.
                pastel  Softer, desaturated colors. This is the default.

                Omitting mode (bare "--tag-colors") is equivalent to
                "--tag-colors=pastel".

    --columns=mode
                Selects the multi-column layout mode. mode is one of:

                compact Column width is normally based on the longest
                        name across every entry, same as classic. But an
                        entry that is unusually long (more than double
                        the width of the "typical" entries) spans
                        multiple column slots on its own row instead of
                        widening every column; the following column(s)
                        simply skip that one row. If this doesn't
                        actually fit more columns than classic would
                        (e.g. no entry is long enough to matter), the
                        classic layout is used instead, since it reads
                        the same with no skipped cells. This is the
                        default behavior.
                classic Always behaves like plain ls -C: column width is
                        fixed at the longest name across every entry,
                        so a single very long name can widen every
                        column.

                Omitting mode (bare "--columns") is equivalent to
                "--columns=compact".

    --tag=mode
                Selects how Finder tags (see COLORS below) are shown
                for each entry. mode is one of:

                bg      Uses the color of the entry's last Finder tag,
                        if any, as the entry's own background. If there
                        are multiple tags, the colors of the others are
                        appended after the name as tightly packed dots
                        (●), ordered from the second-to-last tag back
                        to the first. This is the default behavior.
                dot     Never sets a background color from a Finder
                        tag; every tag (not just the extras) shows as a
                        dot after the name instead, ordered from the
                        last tag back to the first.
                str     Appends every Finder tag's name after each
                        entry, in assignment order, as a bracketed
                        comma-separated list (e.g. "report.pdf [Work,
                        Urgent]"), instead of any dot. A tag with a
                        color is shown in that tag's own color; a tag
                        with no color assigned is shown in the
                        terminal's default foreground color. Never sets
                        a background color from a tag either -- bg and
                        str are mutually exclusive, so str always lists
                        every tag the entry has regardless of whether
                        that tag would otherwise have become the
                        background. With --color=never (or otherwise no
                        color), the names are still listed, just
                        without color. With --stripe, the whole label
                        -- brackets and commas included, not just the
                        tag names -- picks up the entry's striped-
                        column tint, so it reads as part of the same
                        painted block rather than leaving a plain gap.
                off     Never shows a Finder tag in any form -- no
                        background, no dot, no name. Skips querying
                        Finder tags for each entry entirely, rather
                        than just discarding the result.

                Omitting mode (bare "--tag") is equivalent to
                "--tag=bg".

    --stripe    Tints every entry's background, filling the entry's
                full column width, not just the name, alternating
                between two tints by column (0-indexed even columns get
                one tint, odd columns the other), so adjacent columns
                read as distinct bands. In --columns compact mode, an
                entry that spans multiple columns stripes according to
                the column it starts in.

                With --tag=bg (the default), an entry with a Finder tag
                keeps that tag's own color for the name itself; only
                the rest of the column -- the padding after the name --
                gets the stripe tint. An entry with no tag gets the
                stripe tint across the whole column, name included.
                With --tag=dot, --tag=str, or --tag=off, a Finder tag is
                never used as the background at all, so every column
                always gets the stripe tint regardless of whether the
                entry has a tag.

                In -l, there's no column, so the entry's row (odd rows,
                0-indexed) takes the place of a column: the whole line
                -- permissions through the date, and the name -- gets
                the tint (--tag=bg still wins for the name itself; only
                the rest of the line falls back to the stripe). Only
                odd rows are tinted there; even rows are left with no
                background.

                In -1, and in plain non-tty output without -C, there's
                likewise no column, so the entry's row stands in for
                one the same way as in -l; unlike -l, though, there's
                no permissions/owner/size/date text surrounding the
                name to extend the tint across, so only the name itself
                (--tag=bg still winning when it applies) is tinted on
                odd rows. Multi-column output forced there by -C stripes
                by column as usual instead.

    --suffix-color=mode
                Selects the color of the -F type indicator (/ @ * = |)
                appended to an entry. mode is one of:

                off     The indicator takes on the same color as the
                        entry's name (foreground gradient, and any
                        Finder tag or stripe background), i.e. no color
                        of its own. This is the default behavior.
                type    The indicator instead gets its own foreground
                        color keyed by which character it is (see
                        SUFFIX_TYPE_SGR), matching /bin/ls -G's default
                        LSCOLORS for that file type (see its man page):
                        / (directory) blue, @ (symlink) magenta, =
                        (socket) green, | (pipe) yellow, * (executable)
                        red. Always the plain ANSI 8-color codes real ls
                        itself uses, regardless of --color/--tag-colors
                        or light/dark background. The name itself keeps
                        its own color either way.

                Omitting mode (bare "--suffix-color") is equivalent to
                "--suffix-color=off". Has no effect without -F.

    --fg-mode=mode
                Selects whether a name's own foreground color is set
                from its recency gradient. mode is one of:

                date    Colors each name by how recently it was
                        modified (see COLORS below). This is the
                        default behavior.
                off     Leaves names in the terminal's default
                        foreground color. Finder tag and stripe
                        backgrounds are unaffected either way.

                Omitting mode (bare "--fg-mode") is equivalent to
                "--fg-mode=date".

    --base-fg=RRGGBB
                Overrides the color the oldest files (beyond the 1-
                month threshold, see COLORS below) fade to in the
                recency gradient, as a 6-hex-digit RGB value (e.g.
                808080 for gray). Without --base-fg, that endpoint is a
                fixed guess ((0,0,0) black for a light background,
                light gray for a dark one) at the terminal's own
                default text color; --base-fg lets it be stated
                directly instead, since actual terminal foreground
                colors vary widely between users/themes. The whole
                gradient (all 8 steps, from the cyan/magenta starting
                color down to RRGGBB) is recomputed as a straight linear
                interpolation when --base-fg is given, rather than using
                the normal hand-tuned steps. Has no effect with
                --fg-mode=off.

    --quote     Wraps a displayed name in shell quotes whenever it
                contains whitespace, a shell metacharacter (` $ & ; |
                ( ) < > * ? [ ] { } ! " ' \\), or a leading ~ or # (both
                only significant as the first character of a word), so
                it's safe to paste directly into a shell command line.
                Names with none of those are left unquoted. Normally
                single-quoted; if the name itself contains a ', double
                quotes are used instead (escaping $ ` " \\ inside),
                matching GNU ls's --quoting-style=shell. With -F, the
                type indicator is appended after the closing quote, not
                inside it.

                If any name in the listing needs quoting, every
                unquoted name gets a leading space in its place, so the
                opening quote of a quoted name hangs one column to the
                left of its unquoted neighbors' text rather than
                pushing that text out of alignment (matching GNU ls's
                shell quoting style). Applies in both -C (the default
                multi-column layout) and -l. A listing where nothing
                needs quoting is unaffected.

                A name containing a control character (e.g. the CR in
                "Icon\r", the marker for a Finder folder custom icon)
                is, on a terminal, otherwise displayed with each such
                character replaced by '?' (see COLORS below), which
                loses the original bytes. --quote instead uses ANSI-C
                quoting ($'...', bash/zsh syntax, e.g. $'Icon\r'), with
                each such character backslash-escaped, so the displayed
                name pastes back into a shell as the exact original
                name. Such a name doesn't get the hanging-indent
                treatment itself ($'...' opens with 2 characters, not
                1), though it still counts as "needs quoting" for
                deciding whether other names in the listing do.

    -X          Sort by extension: the text after the last '.' in each
                name (no extension sorts first), ties broken by
                whatever order was otherwise in effect. This is a GNU
                ls -X, not a macOS one -- macOS's own /bin/ls -X means
                "don't descend into directories that cross filesystem
                boundaries" during a recursive listing, a completely
                unrelated flag, so this sort is done entirely in
                Python instead of being passed through to ls(1).

    --group-directories-first
                Lists directories before every other entry, stable-
                sorting them to the front so whatever order -t/-S/-X/-r
                (or plain name order) already produced is preserved
                within each group. Directory-ness is checked by
                following symlinks (a symlink to a directory is grouped
                as one, matching GNU ls's own --group-directories-first
                behavior), unlike -F/-B's own lstat-based classification
                (see -F/-B above), which shows a symlink to a directory
                as a symlink, not a directory. Since -l's permission/
                owner/size/date columns come from a separate `ls -l`
                call that has no notion of this reordering, macls.py
                matches each spliced line back up to its real ls -l
                data itself, so grouping never misattributes a line to
                the wrong entry.

    The following options mirror the standard macOS ls(1):

    -a          Show all files, including . and ..

    -A          Show all files except . and ..

    -l          Use long format (permissions, owner, size, date, etc.)

    -h          With -l, show file sizes in human-readable form (e.g.
                1.0K, 234M, 2.3G) instead of raw byte counts. Has no
                effect without -l.

    -1          Force single-column, one-entry-per-line output

    -C          Force multi-column output, even when standard output
                isn't a terminal

                -1, -C, and -l select mutually exclusive display
                formats; when more than one is given, whichever comes
                last on the command line wins (matching real ls's own
                handling of its format options), not just -1 always
                overriding -C.

    -F          Append a type indicator (one of / @ * = |) to entries
                (see --suffix-color for its color)

    -t          Sort by modification time, newest first

    -S          Sort by file size, largest first

    -r          Reverse whatever sort order is otherwise in effect

    -d          List directories themselves, not their contents

    -R          Recursively list subdirectories encountered

    --help      Print a usage message and exit

    --version   Print the version number and exit

    When standard output is a pipe or a file, coloring is disabled by
    default (set the CLICOLOR_FORCE environment variable to force
    coloring regardless); --color overrides both of these.

COLORS
    foreground
        An 8-step gradient based on how recently the file was modified
        (disabled by --fg-mode=off, which leaves names in the
        terminal's default foreground color instead). The steps are
        determined by fixed elapsed-time thresholds (5 min / 30 min /
        1 hour / 2 hours / 1 day / 1 week / 1 month / beyond), each
        mapped to a 24-bit RGB color (see DATE_COLOR_STOPS). If the
        terminal supports 24-bit truecolor
        (advertised via COLORTERM; see supports_truecolor()), the RGB
        value is used directly; otherwise it's converted to the nearest
        ANSI 256-color palette number (see rgb_to_ansi256()).

        Two color families are provided and switched based on the
        background color, so that foreground and background don't clash
        in hue and become hard to read (see FG_FAMILY_FOR_BG,
        NO_BG_FG_FAMILY):

        cyan family
            Starts at RGB(0,255,255) (vivid cyan). Used when the
            background is anything other than green/blue (gray, purple,
            yellow, red, orange).

        magenta family
            Starts at RGB(255,0,255) (vivid magenta). Used when the
            background is green/blue (too close in hue to the cyan
            family to stay readable), and as the default when there is
            no background (no Finder tag).

        Each family additionally has a light-background and a
        dark-background variant (--theme; see detect_dark_background()):
        the light-background stops sink toward black as files age; the
        dark-background stops instead desaturate toward a light gray,
        since fading to black would make old files invisible against a
        dark background. --base-fg overrides that endpoint directly
        (see build_date_color_stops()), for terminals whose own default
        foreground color isn't well approximated by either of those two
        guesses; the whole gradient is then a straight linear
        interpolation from the family's starting color to --base-fg
        instead of the normal hand-tuned steps.

    background
        With --tag=bg (the default), if one or more Finder tags are
        present, the color of the last tag in _kMDItemUserTags (in the
        order the tags were assigned) is used as the background. When
        there are multiple tags, the colors of the other tags are
        appended after the name as tightly packed dots (●), ordered
        from the second-to-last tag back to the first. With --tag=dot,
        every tag (not just the extras) is a dot instead, ordered from
        the last tag back to the first, and no background color is set
        from a Finder tag at all; --tag=str likewise never sets a
        background (see --tag above for its own text-label display),
        and --tag=off shows no tag information at all. If there are no
        tags, no background color is set either way.

        In 24-bit truecolor mode, the Finder tag color itself comes from
        FINDER_COLOR_RGB_BY_MODE, selected by --tag-colors
        (vivid/pastel). In ANSI 256-color mode, --tag-colors has no
        effect; the color always comes from FINDER_COLOR_CODES.

        With --stripe, entries that end up with no Finder tag
        background (see --tag=bg above) instead get a subtle gray tint
        (see STRIPE_BG_RGB/STRIPE_BG_CODE) alternated by the entry's
        starting column in the multi-column grid; with --tag=dot,
        --tag=str, or --tag=off, every entry gets that same tint
        unconditionally, since no Finder tag is ever used as the
        background then. See --stripe above for the details and its
        scope (multi-column, -l, -1, and plain non-tty output; never
        --color=never or otherwise no color).

IMPLEMENTATION NOTES
    Enumerating/sorting directory contents and the -l long-format output
    (permission bits, owner/group, size alignment, date formatting,
    etc.) must match macOS's standard ls behavior exactly; reimplementing
    that from scratch would carry a large regression risk, so it is
    still delegated to the ls(1) command.

    Everything else (fetching Finder tags, computing date colors,
    computing display width, getting terminal width, sorting multiple
    directory arguments) is done entirely in python3, eliminating the
    external process launches (stat/date/tput/sort, and the
    xxd/plutil/grep/tr pipeline for xattr) that the earlier bash version
    needed.

    macOS's Python lacks os.getxattr, so ctypes is used to call libc's
    getxattr(2) directly from the standard library. No external process
    is launched per entry, including for Finder tag retrieval -- except
    for -I's own thumbnails (see below).

    -I shrinks a source image with the sips(1) command before
    base64-encoding/transmitting it, but only once the file is above
    SIPS_RESIZE_THRESHOLD_BYTES: below that, reading and encoding it
    as-is is already fast, and sips's own process-startup cost would be
    the larger expense, not a win. Above it -- a multi-megapixel photo,
    a scanned PDF, an iPhone HEIC -- what's actually slow is
    base64-encoding and transmitting the full-resolution original just
    for iTerm2 to downscale it on arrival, so shrinking it locally
    first (to a size still generous enough to stay sharp on a HiDPI
    display, see SIPS_TARGET_PX_PER_CELL) fixes that. No dependency is
    added: sips ships with macOS itself. See _sips_shrink_image().

    -I also thumbnails Word/Excel/PowerPoint documents, both the modern
    Office Open XML formats and the legacy binary ones (see
    QL_EXTENSIONS), via qlmanage(1), the CLI for macOS's built-in
    Quick Look -- the same generator Finder itself uses, so these get
    an actual rendered first-page/sheet/slide preview rather than a
    generic file icon. There's no original-file-bytes fallback for
    these (an OSC 1337 client can't render a .docx directly), so any
    failure just means no thumbnail for that entry. A "~$name.docx"-
    style lock file left behind while the real document is open
    elsewhere is excluded up front, in build_image_prefix() itself,
    rather than being handed to qlmanage: it isn't actually a valid
    document (just a small owner-info stub with the same extension),
    and qlmanage has been observed to hang on one well past its own
    timeout. See _qlmanage_thumbnail().

    sips's own process-startup/framework-load cost (~200ms, confirmed
    against a real invocation, and largely independent of the image's
    own size) would still add up linearly across a directory of many
    large images if paid serially, so _build_image_prefixes() runs
    build_image_prefix() for a directory's images concurrently on a
    thread pool (see _build_images_parallel()) rather than one at a
    time -- safe since each entry's own thumbnail is independent of
    every other's, and worthwhile since that ~200ms is spent waiting on
    the external sips process, not on the GIL.

    In -1/-l specifically (one entry per physical line, unlike
    multi-column output, where several entries share a line and the
    whole grid's layout has to be known before any of it can be
    printed), list_target() goes a step further and streams: each
    entry's own text is built and ready immediately (an entry's
    img_prefix there is always the same fixed-width blank pad,
    independent of whether that entry even has a thumbnail), so rather
    than collecting the whole directory's thumbnails into a list before
    printing any of it, each line is written as soon as its own
    thumbnail (if it has one) is ready -- see _stream_image_suffixes().
    A directory of many large images no longer has to sit through every
    other entry's sips call before its first line appears.
"""

import base64
import concurrent.futures
import ctypes
import locale
import os
import plistlib
import shutil
import stat as stat_module
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import unicodedata
from dataclasses import dataclass
from typing import Optional

FINDER_TAG_ATTR = "com.apple.metadata:_kMDItemUserTags"
FINDER_TAG_ATTR_BYTES = FINDER_TAG_ATTR.encode("utf-8")

# macOS's getxattr(2) has a 6-argument signature, unlike Linux.
# options=0 follows symlink targets, matching xattr(1)'s default.
_GETXATTR = ctypes.CDLL(None, use_errno=True).getxattr
_GETXATTR.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_int,
]
_GETXATTR.restype = ctypes.c_ssize_t

# For -I (image thumbnails). Follows imgls's (bundled with iTerm2)
# default settings: a height of 1 cell (with the matching narrow width
# below) so subsequent text can continue on the same line without
# cursor control. This is the base (--scale=1) size; see --scale below.
ITERM_IMG_WIDTH = 2
ITERM_IMG_HEIGHT = 1

# --scale=n (see list_target()'s scale_applies) multiplies both
# ITERM_IMG_WIDTH and ITERM_IMG_HEIGHT by n for a bigger thumbnail --
# only in -1 or -l, the two single-line-per-entry contexts -I itself is
# ever active in to begin with (it's disabled outright on non-tty
# output regardless of --scale -- see main()), where per iTerm2's own
# inline-image protocol,
# the cursor after a taller image lands at the end of the image's own
# last line, ready for that entry's name to continue right after it,
# same as height 1's single-row case (confirmed against a real iTerm2
# session: a multi-row thumbnail doesn't overlap the next entry). In
# multi-column output, several entries' worth of text share one
# physical line, so a taller thumbnail would misalign them; --scale is
# ignored there (silently capped to 1), same as e.g. -h having no
# effect without -l.
#
# The width is scaled by the same factor as the height (not left at
# ITERM_IMG_WIDTH) because preserveAspectRatio=1 (see
# build_image_prefix()) fits the image within its width x height box
# without exceeding either dimension: scaling only the height left most
# photos -- wider than they are tall -- still bounded by the unchanged
# width, with the extra height going unused as blank space.

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp",
    ".tiff", ".tif", ".webp", ".heic", ".heif",
    ".pdf"
}

# -I extensions whose thumbnail comes from macOS's Quick Look (via
# qlmanage(1) -- see _qlmanage_thumbnail()) rather than being read
# directly: unlike IMAGE_EXTENSIONS, these aren't image files
# themselves, so there's no raw bytes to fall back to sending if
# thumbnail generation fails. Currently just Word/Excel/PowerPoint
# documents, both the modern XML-based Office Open XML formats and the
# legacy binary ones (confirmed against real .xls/.ppt files to render
# an actual first-page/sheet/slide preview, same as the XML formats do,
# out of the box with no Office installation needed, via macOS's own
# Preview.app/QuickLook generators) -- but Quick Look itself isn't
# limited to Office documents, so this is named/kept separate from any
# one file family: any other extension with a real (non-generic-icon)
# Quick Look generator is a candidate to add here later.
QL_EXTENSIONS = {".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt"}

# build_image_prefix() only bothers shelling out to sips(1) to shrink a
# source image before base64-encoding/transmitting it once the file is
# at least this big -- below this, reading+encoding the file as-is is
# already fast enough that sips's own process-startup overhead would be
# the larger cost, not a win. Above it (a multi-megapixel photo, a
# scanned PDF, etc.), what's actually slow is base64-encoding and
# transmitting the *original* full-resolution file to the terminal only
# for iTerm2 to downscale it there -- shrinking it locally first fixes
# that.
SIPS_RESIZE_THRESHOLD_BYTES = 512 * 1024

# Extensions build_image_prefix() never tries to shrink via sips even
# above SIPS_RESIZE_THRESHOLD_BYTES: sips flattens an animated GIF to
# its first frame, which would silently kill iTerm2's own inline
# playback of an animated thumbnail.
SIPS_RESIZE_SKIP_EXTENSIONS = {".gif"}

# Rough pixels-per-cell estimate used to size the sips resize target
# (see _sips_shrink_image()) from a thumbnail's width in terminal
# cells: generous enough to stay sharp on a HiDPI display at any
# --scale, while still shrinking a multi-megapixel source by an order
# of magnitude or more.
SIPS_TARGET_PX_PER_CELL = 60
SIPS_TARGET_PX_MIN = 256

# JPEG quality (sips -s formatOptions) for _sips_shrink_image()'s
# output -- a thumbnail only a couple hundred pixels across doesn't
# need print-quality encoding, so this trades a bit more compression
# artifacting (invisible at that size) for a smaller payload than a
# higher setting would give.
SIPS_JPEG_QUALITY = 80

# Finder tag color number (1-7) -> ANSI 256-color palette number (raw
# value shared by fg/bg)
FINDER_COLOR_CODES = {
    1: "244",  # Gray
    2: "2",    # Green
    3: "5",    # Purple
    4: "33",   # Blue
    5: "3",    # Yellow
    6: "1",    # Red
    7: "208",  # Orange
}

# Finder tag color number (1-7) -> approximate 24-bit RGB, used by the
# truecolor renderer instead of FINDER_COLOR_CODES (see finder_sgr()).
# Two variants are provided, selected by --tag-colors (see
# FINDER_COLOR_RGB_BY_MODE): "vivid" (the default, saturated colors
# matching the Finder tag hues) and "pastel" (softer, desaturated
# colors, e.g. for a less harsh look against a dark background).
FINDER_COLOR_RGB_VIVID = {
    1: (128, 128, 128),  # Gray
    2: (0, 128, 0),      # Green
    3: (128, 0, 128),    # Purple
    4: (0, 135, 255),    # Blue
    5: (128, 128, 0),    # Yellow
    6: (128, 0, 0),      # Red
    7: (255, 135, 0),    # Orange
}
FINDER_COLOR_RGB_PASTEL = {
    1: (190, 190, 190),  # Gray
    2: (152, 251, 152),  # Green
    3: (216, 191, 216),  # Purple
    4: (173, 216, 230),  # Blue
    5: (255, 255, 153),  # Yellow
    6: (255, 160, 160),  # Red
    7: (255, 200, 150),  # Orange
}
FINDER_COLOR_RGB_BY_MODE = {
    "vivid": FINDER_COLOR_RGB_VIVID,
    "pastel": FINDER_COLOR_RGB_PASTEL,
}

# --suffix-color=type's per-type color for -F's type indicator (/ @ * = |),
# matching /bin/ls -G's default LSCOLORS (see its man page): directory
# blue, symlink magenta, socket green, pipe (FIFO) yellow, executable
# red. Plain standard ANSI 8-color SGR foreground codes (30-37), same as
# real ls itself emits -- not the 24-bit truecolor/256-color palette
# used elsewhere in this file, and not adjusted for light/dark
# background, since real ls doesn't do either.
SUFFIX_TYPE_SGR = {
    "/": "34",  # directory: blue
    "@": "35",  # symlink: magenta
    "=": "32",  # socket: green
    "|": "33",  # pipe (FIFO): yellow
    "*": "31",  # executable: red
}

# --stripe background for entries with no Finder tag, alternated
# by the entry's starting column in the multi-column grid: every column
# gets a background tint, even columns (0-indexed 1, 3, 5, ...) using
# the alt=False entry below and odd columns (0-indexed 0, 2, 4, ...)
# using alt=True, so adjacent columns read as visually distinct bands.
# Subtle gray tints rather than hues, so they read as a grouping cue
# without competing with the foreground gradient or Finder tag colors.
# Indexed as [theme][alt] ("light"/"dark", see opts.theme); theme
# selects between the two variants the same way it does for the
# foreground gradient stops. Each per-theme entry is a (alt=False,
# alt=True) pair -- indexable directly with a bool since bool is an int
# subclass in Python (False == 0, True == 1).
STRIPE_BG_RGB = {
    "light": ((235, 239, 222), (215, 223, 189)),  # pale gray-green, slightly darker pale gray-green
    "dark": ((35, 35, 35), (20, 20, 20)),         # faint gray, slightly darker faint gray
}
STRIPE_BG_CODE = {
    "light": ("254", "187"),  # ANSI 256
    "dark": ("236", "238"),   # ANSI 256
}

# Elapsed-time thresholds used by DATE_COLOR_STOPS_* below (seconds).
AGE_5_MINUTES = 300
AGE_30_MINUTES = 1800
AGE_1_HOUR = 3600
AGE_2_HOURS = 7200
AGE_1_DAY = 86400
AGE_1_WEEK = 604800
AGE_1_MONTH = 2592000

# For foreground: maps recency of file modification to a color, as a
# list of (max_age_seconds, (r, g, b)) stops in newest-first order. The
# last stop's max_age_seconds is None, meaning "no upper bound" (used
# for any age not covered by an earlier stop). Storing plain 24-bit RGB
# keeps this table renderer-agnostic: it's used directly by the
# truecolor (24-bit) renderer, and converted to an ANSI 256-color
# palette number via rgb_to_ansi256() for the 256-color renderer.
#
# Two variants of each family are provided, selected by the detected
# (or user-specified) terminal background lightness (see
# detect_dark_background()). The "lightbg" stops sink toward black as
# files age, reading as "fading out" against a light background; the
# "darkbg" stops instead desaturate toward a light gray, since fading
# to black would make old files invisible against a dark background.
# Cyan family: R fixed at 0, G and B stepped down.
DATE_COLOR_STOPS_CYAN_LIGHTBG = [
    (AGE_5_MINUTES, (0, 255, 255)),
    (AGE_30_MINUTES, (0, 255, 215)),
    (AGE_1_HOUR, (0, 215, 215)),
    (AGE_2_HOURS, (0, 215, 175)),
    (AGE_1_DAY, (0, 175, 175)),
    (AGE_1_WEEK, (0, 135, 135)),
    (AGE_1_MONTH, (0, 95, 95)),
    (None, (0, 0, 0)),
]
DATE_COLOR_STOPS_CYAN_DARKBG = [
    (AGE_5_MINUTES, (0, 255, 255)),
    (AGE_30_MINUTES, (40, 230, 230)),
    (AGE_1_HOUR, (80, 210, 210)),
    (AGE_2_HOURS, (110, 195, 195)),
    (AGE_1_DAY, (140, 180, 180)),
    (AGE_1_WEEK, (165, 175, 175)),
    (AGE_1_MONTH, (185, 185, 185)),
    (None, (200, 200, 200)),
]
# Magenta family: G fixed at 0, R and B stepped down.
DATE_COLOR_STOPS_MAGENTA_LIGHTBG = [
    (AGE_5_MINUTES, (255, 0, 255)),
    (AGE_30_MINUTES, (255, 0, 215)),
    (AGE_1_HOUR, (215, 0, 215)),
    (AGE_2_HOURS, (215, 0, 175)),
    (AGE_1_DAY, (175, 0, 175)),
    (AGE_1_WEEK, (135, 0, 135)),
    (AGE_1_MONTH, (95, 0, 95)),
    (None, (0, 0, 0)),
]
DATE_COLOR_STOPS_MAGENTA_DARKBG = [
    (AGE_5_MINUTES, (255, 0, 255)),
    (AGE_30_MINUTES, (230, 40, 230)),
    (AGE_1_HOUR, (210, 80, 210)),
    (AGE_2_HOURS, (195, 110, 195)),
    (AGE_1_DAY, (180, 140, 180)),
    (AGE_1_WEEK, (175, 165, 165)),
    (AGE_1_MONTH, (185, 185, 185)),
    (None, (200, 200, 200)),
]

# (family, theme) -> the stops table to use. theme is "light" or "dark"
# (see opts.theme, resolved from --theme's auto/light/dark by main()).
DATE_COLOR_STOPS = {
    ("cyan", "light"): DATE_COLOR_STOPS_CYAN_LIGHTBG,
    ("cyan", "dark"): DATE_COLOR_STOPS_CYAN_DARKBG,
    ("magenta", "light"): DATE_COLOR_STOPS_MAGENTA_LIGHTBG,
    ("magenta", "dark"): DATE_COLOR_STOPS_MAGENTA_DARKBG,
}

# Each family's starting (newest-file) color, used as one endpoint of
# build_date_color_stops()'s interpolation for --base-fg -- the other
# endpoint of DATE_COLOR_STOPS_*'s own first stop, factored out here so
# it doesn't need to be duplicated/hardcoded again there.
FG_FAMILY_START_RGB = {
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
}

# The (max_age_seconds, ...) thresholds DATE_COLOR_STOPS_* itself uses,
# factored out so build_date_color_stops() can reuse the exact same
# shape for a --base-fg-interpolated table.
DATE_COLOR_AGE_THRESHOLDS = (
    AGE_5_MINUTES, AGE_30_MINUTES, AGE_1_HOUR, AGE_2_HOURS,
    AGE_1_DAY, AGE_1_WEEK, AGE_1_MONTH, None,
)


def build_date_color_stops(start_rgb, end_rgb):
    """Builds an 8-step (max_age, rgb) stops list, the same shape as
    DATE_COLOR_STOPS_CYAN_LIGHTBG etc. (see DATE_COLOR_AGE_THRESHOLDS),
    by linearly interpolating from start_rgb (a family's own vivid
    starting color, see FG_FAMILY_START_RGB) to end_rgb across those
    same thresholds. Used instead of the hand-tuned DATE_COLOR_STOPS_*
    tables when --base-fg overrides the color the oldest files fade to
    -- those tables' own endpoints ((0, 0, 0) for a light background, a
    light gray for a dark one) are just one arbitrary guess at the
    terminal's actual default foreground color, which --base-fg lets a
    user instead state directly (see parse_hex_rgb()).

    Returns the list of (max_age, (r, g, b)) stops."""
    n = len(DATE_COLOR_AGE_THRESHOLDS)
    return [
        (
            max_age,
            tuple(round(s + (e - s) * i / (n - 1)) for s, e in zip(start_rgb, end_rgb)),
        )
        for i, max_age in enumerate(DATE_COLOR_AGE_THRESHOLDS)
    ]

# Which foreground family ("cyan" or "magenta") to use per background
# (Finder tag number). Only the combinations that are too close in hue
# to stay readable (green/blue against the cyan family) switch to the
# magenta family. Numbers not listed here (gray, purple, yellow, red,
# orange) use the cyan family.
FG_FAMILY_FOR_BG = {
    1: "cyan",     # Gray
    2: "magenta",  # Green
    3: "cyan",     # Purple
    4: "magenta",  # Blue
    5: "cyan",     # Yellow
    6: "cyan",     # Red
    7: "cyan",     # Orange
}

# Default foreground family for files with no background (no Finder tag).
NO_BG_FG_FAMILY = "magenta"

PROG = "macls.py"
VERSION = "1.1.0-dev"


def finder_color_code(num):
    """Returns the ANSI 256-color code string for Finder tag color
    number num (see FINDER_COLOR_CODES), or "" if num has none."""
    return FINDER_COLOR_CODES.get(num, "")


def rgb_to_ansi256(rgb):
    """Converts an arbitrary 24-bit (r, g, b) tuple to the nearest ANSI
    256-color palette number, for terminals/renderers that don't support
    24-bit truecolor. (0, 0, 0) maps to 0 (the standard ANSI black)
    rather than the nearest 6x6x6-cube black (16), matching prior
    behavior for the (light-background) stops that end at pure black.
    Grayscale RGB is mapped onto the 24-step grayscale ramp
    (codes 232-255) when that's a closer match than the 6x6x6 color
    cube (codes 16-231), which it usually is.

    Returns the color number as a decimal string (ready to drop into an
    SGR escape sequence)."""
    r, g, b = rgb
    if (r, g, b) == (0, 0, 0):
        return "0"
    if r == g == b:
        if r < 8:
            return "16"
        if r > 248:
            return "231"
        return str(round((r - 8) / 247 * 24) + 232)
    ri = round(r / 255 * 5)
    gi = round(g / 255 * 5)
    bi = round(b / 255 * 5)
    return str(16 + 36 * ri + 6 * gi + bi)


def date_color_rgb(mtime, now, bg_num, theme, base_fg=None):
    """Maps recency of modification to a 24-bit (r, g, b) color. Selects
    the color family ("cyan"/"magenta") from FG_FAMILY_FOR_BG based on
    bg_num (the Finder tag number used for the background); if bg_num is
    None (no background), uses NO_BG_FG_FAMILY. theme ("light" or
    "dark", see opts.theme) picks between the light-background and
    dark-background stops tables for that family (see DATE_COLOR_STOPS).
    base_fg (see --base-fg), if given (an (r, g, b) tuple), overrides
    the color the oldest files fade to: the family's own stops table is
    replaced with one interpolated straight from that family's vivid
    starting color to base_fg (see build_date_color_stops()), ignoring
    theme -- a user-specified base_fg is assumed to already be the right
    color for their own terminal, light or dark. Returns None if mtime
    is None."""
    if mtime is None:
        return None
    family = FG_FAMILY_FOR_BG.get(bg_num, "cyan") if bg_num is not None else NO_BG_FG_FAMILY
    if base_fg is not None:
        stops = build_date_color_stops(FG_FAMILY_START_RGB[family], base_fg)
    else:
        stops = DATE_COLOR_STOPS[(family, theme)]
    age = now - mtime
    if age < 0:
        age = 0
    for max_age, rgb in stops:
        if max_age is None or age <= max_age:
            return rgb
    return stops[-1][1]


def fg_sgr(rgb, use_truecolor):
    """Returns the SGR parameter string for setting the foreground color
    to rgb: 24-bit truecolor (38;2;r;g;b) or the nearest ANSI 256-color
    palette entry (38;5;n), depending on use_truecolor."""
    if use_truecolor:
        r, g, b = rgb
        return f"38;2;{r};{g};{b}"
    return f"38;5;{rgb_to_ansi256(rgb)}"


def finder_sgr(num, ground, use_truecolor, tag_colors="pastel"):
    """Returns the SGR parameter string for Finder tag color num.
    ground is "38" (foreground, used for the extra-tag dots) or "48"
    (background, used for the last tag). In truecolor mode, uses
    FINDER_COLOR_RGB_BY_MODE[tag_colors] ("vivid" or "pastel", see
    --tag-colors); otherwise uses FINDER_COLOR_CODES directly (rather
    than deriving it from RGB via rgb_to_ansi256()), since it
    deliberately reuses macOS Terminal's theme-adjustable standard color
    slots for some tags, which a plain RGB match would lose. tag_colors
    is ignored outside truecolor mode."""
    if use_truecolor:
        rgb_table = FINDER_COLOR_RGB_BY_MODE.get(tag_colors, FINDER_COLOR_RGB_VIVID)
        r, g, b = rgb_table.get(num, (0, 0, 0))
        return f"{ground};2;{r};{g};{b}"
    code = finder_color_code(num)
    return f"{ground};5;{code}"


def stripe_sgr(use_truecolor, theme, alt=False):
    """Returns the background SGR parameter string for --stripe's
    tint. theme is "light" or "dark" (see opts.theme). alt selects
    which of the two color variants to use (see
    STRIPE_BG_RGB/STRIPE_BG_CODE) so a multi-column caller can alternate
    it by the entry's column parity, giving adjacent columns two
    distinct tints."""
    if use_truecolor:
        r, g, b = STRIPE_BG_RGB[theme][alt]
        return f"48;2;{r};{g};{b}"
    return f"48;5;{STRIPE_BG_CODE[theme][alt]}"


def get_finder_tags(path):
    """Returns the Finder tags for the given path as (name, color_num)
    pairs, in the order they were assigned. color_num is 0 for a tag
    with no color assigned (or an unparseable one). Returns an empty
    list if there are no tags or retrieval fails.

    macOS's python3 doesn't have os.getxattr, so ctypes is used to call
    libc's getxattr(2) directly. The first call gets the value's size,
    and the second reads the binary plist. No external process is
    launched.
    """
    try:
        encoded_path = os.fsencode(path)
        size = _GETXATTR(
            encoded_path, FINDER_TAG_ATTR_BYTES, None, 0, 0, 0
        )
        if size <= 0:
            return []
        buffer = ctypes.create_string_buffer(size)
        length = _GETXATTR(
            encoded_path, FINDER_TAG_ATTR_BYTES, buffer, size, 0, 0
        )
    except (OSError, TypeError, ValueError):
        return []
    if length < 0:
        return []
    try:
        raw = buffer.raw[:length]
        tags = plistlib.loads(raw)
    except Exception:
        return []

    result = []
    for tag in tags:
        name, suffix = tag.rsplit("\n", 1) if "\n" in tag else (tag, "")
        num = int(suffix) if suffix.isdigit() else 0
        result.append((name, num))
    return result


def get_finder_tag_nums(path):
    """Returns the Finder tag color numbers for the given path, in the
    order they were assigned (tags without a color are skipped). Returns
    an empty list if there are no tags or retrieval fails. See
    get_finder_tags()."""
    return [num for _, num in get_finder_tags(path) if num != 0]


def display_width(name):
    """The actual display width of a name (2 for full-width characters,
    1 for half-width). macOS's filesystem returns filenames in NFD
    (decomposed form, e.g. dakuten/handakuten as combining characters),
    so counting width character-by-character without normalizing would
    overcount by the combining characters. Since terminals render a
    combining character together with its base as a single full-width
    character, the name is normalized to NFC (composed form) before
    computing width. Any combining characters remaining after NFC
    normalization are treated as width 0.
    """
    normalized = unicodedata.normalize("NFC", name)
    return sum(
        0 if unicodedata.combining(ch)
        else 2 if unicodedata.east_asian_width(ch) in ("W", "F")
        else 1
        for ch in normalized
    )


def sanitize_display_name(name):
    """Replaces control/invisible characters (newline, CR, tab, etc.)
    with '?'. macOS's standard ls replaces non-printable characters with
    '?' by default when writing to a terminal (equivalent to -q). This
    script captures ls's output via a pipe, so that substitution doesn't
    happen automatically; a name like "Icon\\r" (containing a CR, the
    marker used for Finder folder custom icons) would otherwise send a
    raw CR to the terminal and reset the cursor to the start of the line,
    corrupting the display. So the display name is sanitized here on its
    own.

    Returns the sanitized copy of name.
    """
    return "".join(
        ch if unicodedata.category(ch)[0] != "C" else "?" for ch in name
    )


# Characters (beyond whitespace) that make a name unsafe to paste
# unquoted into a POSIX shell: substitution/expansion (` $), control
# operators (& ; | ( ) < >), globbing (* ? [ ] { }), history (!),
# quoting itself (" ' \). ~ and # are deliberately excluded here --
# both only trigger (tilde-expansion / comment-start) as the leading
# character of a word, so needs_shell_quoting() checks them
# separately (matching GNU ls's --quoting-style=shell, confirmed
# against `gls`, which likewise only quotes for a leading ~ or #).
# Used by needs_shell_quoting() below.
SHELL_METACHARS = set("`$&;|()<>*?[]{}!\"'\\")


def needs_shell_quoting(name):
    """Whether name contains whitespace or a shell metacharacter
    (SHELL_METACHARS), or starts with ~ or # (see SHELL_METACHARS
    above), and so isn't safe to paste as-is into a shell command
    line (see --quote). Returns a bool."""
    return name[:1] in ("~", "#") or any(
        ch.isspace() or ch in SHELL_METACHARS for ch in name
    )


def shell_quote(name):
    """Wraps name in POSIX shell quotes, matching GNU ls's
    --quoting-style=shell: single quotes normally, but double quotes
    instead when name contains an embedded single quote (avoids the
    close-quote/escaped-quote/reopen-quote run '\\'' that plain
    single-quoting would otherwise need). Inside double quotes, only
    $ ` " \\ are shell-special and need backslash-escaping -- glob
    characters like * ? [ ] stay literal there. See --quote.

    Returns the quoted string."""
    if "'" in name:
        escaped = "".join(
            "\\" + ch if ch in "$`\"\\" else ch for ch in name
        )
        return '"' + escaped + '"'
    return "'" + name + "'"


# bash/zsh ANSI-C quoting ($'...') named escapes for the control
# characters that have one, keyed by codepoint. Anything else caught by
# needs_ansi_c_quoting() falls back to \xHH (or \uHHHH above U+00FF) in
# ansi_c_quote().
ANSI_C_NAMED_ESCAPES = {
    0x07: "\\a",
    0x08: "\\b",
    0x09: "\\t",
    0x0A: "\\n",
    0x0B: "\\v",
    0x0C: "\\f",
    0x0D: "\\r",
}


def needs_ansi_c_quoting(name):
    """Whether name contains a control/invisible character (the same
    Unicode-category test sanitize_display_name() uses to decide what
    to replace with '?') and so can't be represented, on a terminal, by
    plain single-quoting (see --quote) -- POSIX '...' preserves such
    bytes literally rather than escaping them, and a raw control byte
    sent straight to a terminal (e.g. the CR in "Icon\\r", the marker
    for a Finder folder custom icon) corrupts the display same as if it
    weren't quoted at all. Returns a bool."""
    return any(unicodedata.category(ch)[0] == "C" for ch in name)


def ansi_c_quote(name):
    """Wraps name in bash/zsh ANSI-C quoting ($'...'), the GNU
    ls --quoting-style=shell-escape approach: every control/invisible
    character becomes a backslash escape (a named one from
    ANSI_C_NAMED_ESCAPES if it has one, else \\xHH, or \\uHHHH above
    U+00FF) instead of being silently replaced with '?', so pasting the
    displayed name into a shell reproduces the exact original bytes.
    Literal backslashes and single quotes are also escaped, since both
    are meaningful inside $'...'. See --quote/needs_ansi_c_quoting().

    Returns the quoted string.
    """
    out = ["$'"]
    for ch in name:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "'":
            out.append("\\'")
        elif unicodedata.category(ch)[0] == "C":
            cp = ord(ch)
            if cp in ANSI_C_NAMED_ESCAPES:
                out.append(ANSI_C_NAMED_ESCAPES[cp])
            elif cp <= 0xFF:
                out.append(f"\\x{cp:02x}")
            else:
                out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    out.append("'")
    return "".join(out)


def type_suffix(path):
    """File type indicator for -F (ls -F compatible: / @ * = |). Returns
    that single-character suffix, or "" if path's type gets none."""
    if os.path.islink(path):
        return "@"
    if os.path.isdir(path):
        return "/"
    try:
        mode = os.stat(path).st_mode
    except OSError:
        return ""
    if stat_module.S_ISFIFO(mode):
        return "|"
    if stat_module.S_ISSOCK(mode):
        return "="
    if stat_module.S_ISREG(mode) and os.access(path, os.X_OK):
        return "*"
    return ""


def detect_dark_background():
    """Best-effort detection of whether the terminal's background is
    dark, based on the COLORFGBG environment variable (set by iTerm2 and
    several other terminals as "fg;bg", using the standard 16-color
    ANSI numbers). Returns True/False, or None if the variable isn't set
    or can't be parsed (unknown), in which case the caller should fall
    back to a default rather than guess."""
    value = os.environ.get("COLORFGBG")
    if not value:
        return None
    try:
        bg = int(value.split(";")[-1])
    except ValueError:
        return None
    # 0-6 are the dark half of the standard 16-color palette (black,
    # red, green, yellow, blue, magenta, cyan); 8 is bright black
    # (gray), also dark. The rest (7, 9-15) are light.
    return bg in (0, 1, 2, 3, 4, 5, 6, 8)


def supports_truecolor():
    """Whether the terminal advertises 24-bit truecolor support via the
    (informal but widely honored) COLORTERM environment variable.
    Returns a bool."""
    return os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit")


def iterm2_supported():
    """Whether running in a terminal (iTerm2) that supports the inline
    image protocol (OSC 1337). Also checks LC_TERMINAL, which iTerm2
    sets, for cases like over SSH where the terminal app can't be
    detected directly. Returns a bool."""
    return (
        os.environ.get("TERM_PROGRAM") == "iTerm.app"
        or os.environ.get("LC_TERMINAL") == "iTerm2"
    )


def _png_pixel_size(data):
    """Returns (width, height) in pixels for PNG bytes (the IHDR chunk
    is always the first chunk, at a fixed offset), or None if data isn't
    a well-formed PNG. See get_image_pixel_size()."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def _gif_pixel_size(data):
    """Returns (width, height) in pixels for GIF bytes (the logical
    screen descriptor immediately follows the 6-byte "GIF87a"/"GIF89a"
    signature), or None if data isn't a well-formed GIF. See
    get_image_pixel_size()."""
    if len(data) < 10 or data[:6] not in (b"GIF87a", b"GIF89a"):
        return None
    return struct.unpack("<HH", data[6:10])


def _bmp_pixel_size(data):
    """(width, height) in pixels for BMP bytes (from the DIB header
    that follows the 14-byte file header; width/height are signed --
    a negative height just means the pixel rows are stored top-down,
    irrelevant to the aspect ratio this is used for, so its absolute
    value is returned), or None if data isn't a well-formed BMP. See
    get_image_pixel_size()."""
    if len(data) < 26 or data[:2] != b"BM":
        return None
    width, height = struct.unpack("<ii", data[18:26])
    return abs(width), abs(height)


# JPEG marker codes (see _jpeg_pixel_size()) that carry no length-
# prefixed segment to skip over: SOI/EOI and the RST0-RST7 markers.
_JPEG_MARKERS_WITHOUT_SEGMENT = frozenset({0xD8, 0xD9, *range(0xD0, 0xD8)})
# JPEG SOF (Start Of Frame) marker codes -- one of these carries the
# image's own pixel width/height; 0xC4/0xC8/0xCC are excluded despite
# falling in the same 0xC0-0xCF range since they're DHT/JPG/DAC, not
# SOF markers (see _jpeg_pixel_size()).
_JPEG_SOF_MARKERS = frozenset(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}


def _jpeg_pixel_size(data):
    """Returns (width, height) in pixels for JPEG bytes, found by
    scanning its marker segments for a SOF (Start Of Frame) marker,
    whose payload starts with 1 byte of sample precision followed by
    the image's own 2-byte height then 2-byte width (see
    _JPEG_SOF_MARKERS) -- or None if data isn't a well-formed JPEG or no
    SOF marker is found. See get_image_pixel_size()."""
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None
    i = 2
    n = len(data)
    while i < n - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in _JPEG_MARKERS_WITHOUT_SEGMENT:
            i += 2
            continue
        if i + 4 > n:
            break
        seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
        if marker in _JPEG_SOF_MARKERS:
            if i + 9 > n:
                break
            height, width = struct.unpack(">HH", data[i + 5 : i + 9])
            return width, height
        i += 2 + seg_len
    return None


# Extension (see IMAGE_EXTENSIONS) -> parser function for
# get_image_pixel_size() -- only these 4 formats' pixel dimensions can
# be read with a small amount of stdlib-only header parsing (no
# external imaging library like Pillow); the remaining IMAGE_EXTENSIONS
# formats (TIFF's tag-based IFD structure, WebP's several very
# differently bit-packed sub-formats, HEIC/HEIF's nested ISOBMFF box
# structure, and PDF, where a page's /MediaBox is a page geometry size
# in points, not an embedded image's pixel dimensions) would each need
# meaningfully more parsing code, so their thumbnails keep using the
# flat, unscaled-by-aspect-ratio height instead (see build_image_prefix()).
IMAGE_PIXEL_SIZE_PARSERS = {
    ".png": _png_pixel_size,
    ".gif": _gif_pixel_size,
    ".bmp": _bmp_pixel_size,
    ".jpg": _jpeg_pixel_size,
    ".jpeg": _jpeg_pixel_size,
}


def get_image_pixel_size(data, ext):
    """Returns (width, height) in pixels for image file contents data
    with extension ext (see IMAGE_PIXEL_SIZE_PARSERS), or None if ext
    isn't one of the 4 supported formats or data couldn't be parsed as
    one (a truncated/corrupt file, or an extension that doesn't
    actually match its contents)."""
    parser = IMAGE_PIXEL_SIZE_PARSERS.get(ext)
    if parser is None:
        return None
    try:
        return parser(data)
    except struct.error:
        return None


# Rough approximation of a terminal cell's own height-to-width ratio in
# pixels (e.g. an 8x17px cell -- common for monospace terminal fonts --
# is roughly 2:1), used by build_image_prefix() to convert an image's
# own pixel aspect ratio into a cell row count for a fixed cell column
# width. Real fonts vary (this isn't queried from the actual terminal,
# which Python's stdlib has no portable way to do), so this is only a
# guess -- preserveAspectRatio=1 in the OSC 1337 params still lets
# iTerm2 fit the image within the resulting box if this guess is off,
# same safety net as when no aspect ratio could be determined at all.
CELL_ASPECT_RATIO = 2.0


def _sips_shrink_image(data, ext, max_px):
    """Best-effort shrink of image file contents data (extension ext)
    to at most max_px on its longest side, by shelling out to macOS's
    built-in sips(1) -- returns the shrunk file's bytes (always
    re-encoded as JPEG, at SIPS_JPEG_QUALITY, since that's the one
    lossy format get_image_pixel_size() reads and sips writes reliably
    for every input format IMAGE_EXTENSIONS accepts, PDF included,
    where it rasterizes just the first page), or None on any failure
    (sips missing, an unsupported/corrupt input, a timeout, ...), in
    which case the caller is expected to fall back to sending data
    unshrunk.

    JPEG over PNG trades away alpha transparency (a JPEG thumbnail of a
    source with an alpha channel gets it flattened against an opaque
    background by sips) for a meaningfully smaller thumbnail on
    photographic content, which is what SIPS_RESIZE_THRESHOLD_BYTES
    mostly selects for in the first place (large photos/scans, not
    small graphics) -- acceptable since this is only ever a thumbnail,
    not the original file.

    sips only reads/writes real files, not stdin/stdout, so this writes
    data to a temporary input file (preserving ext, since sips
    dispatches on the input filename's extension) and reads the result
    back from a second temporary output file; both are removed before
    returning.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as in_f:
            in_f.write(data)
            in_path = in_f.name
    except OSError:
        return None
    out_path = in_path + ".out.jpg"
    try:
        result = subprocess.run(
            [
                "sips", "-Z", str(max_px),
                "-s", "format", "jpeg",
                "-s", "formatOptions", str(SIPS_JPEG_QUALITY),
                in_path, "--out", out_path,
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
        )
        if result.returncode != 0:
            return None
        with open(out_path, "rb") as out_f:
            return out_f.read()
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        for p in (in_path, out_path):
            try:
                os.remove(p)
            except OSError:
                pass


def _qlmanage_thumbnail(path, max_px):
    """Best-effort thumbnail for a QL_EXTENSIONS file via macOS's
    built-in Quick Look, shelled out to via qlmanage(1) -- the same
    generator Finder itself uses to preview/icon these files. For the
    Word/Excel/PowerPoint documents QL_EXTENSIONS currently lists --
    modern (.docx/.xlsx/.pptx) or legacy (.doc/.xls/.ppt) -- that means
    an actual rendered first-page/sheet/slide preview rather than a
    generic file icon. Returns the result
    re-encoded as JPEG (via _sips_shrink_image(), reusing the same
    shrink-to-max_px/JPEG-quality logic used for an oversized source
    image), or None on any failure (qlmanage missing, no Quick Look
    generator for this file, a timeout, ...) -- unlike an oversized
    source image, there's no original-file-bytes fallback that would
    make sense to send instead of a thumbnail here, so the caller shows
    no thumbnail at all for this entry in that case.

    qlmanage only writes into a directory (-o), naming its output
    "<original filename>.png" inside it, so this uses a dedicated
    temporary directory per call to avoid collisions with any other
    concurrent call (see _build_images_parallel()/
    _stream_image_suffixes()) and removes it before returning.
    """
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="macls-ql-")
        result = subprocess.run(
            ["qlmanage", "-t", "-s", str(max_px), "-o", tmp_dir, path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
        )
        if result.returncode != 0:
            return None
        out_path = os.path.join(tmp_dir, os.path.basename(path) + ".png")
        with open(out_path, "rb") as f:
            png_data = f.read()
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    return _sips_shrink_image(png_data, ".png", max_px)


def build_image_prefix(path, width=ITERM_IMG_WIDTH, height=ITERM_IMG_HEIGHT, no_sips=False, allow_taller=True):
    """Returns the escape sequence that renders the image at path as a
    thumbnail of `width` cells wide using iTerm2's inline image
    protocol (OSC 1337).

    allow_taller must be False in multi-column output, where several
    entries share one physical line: there, every thumbnail has to fit
    the caller's own `height` exactly (1 row, unscaled by --scale, see
    list_target()) since a taller one would visibly overlap whatever
    comes after it on that same line, or on the row below (confirmed
    against a real iTerm2 session -- and reported as a bug once the
    aspect-ratio height computation below started actually being able
    to compute a >1 height for a portrait/tall source image, which a
    fixed flat height standing in for every image never could). It must
    be True (the default) for -1/-l, the only contexts a taller
    thumbnail is safe in (see _build_image_prefixes()'s own docstring).

    no_sips (see --no-sips) skips the sips(1)-based shrink step below
    entirely, sending the source file at its original resolution
    regardless of size -- the pre-sips behavior, kept only for
    comparing/debugging sips's own effect.

    For the 4 formats get_image_pixel_size() can read (PNG/GIF/BMP/
    JPEG), the height actually used is computed from the image's own
    real pixel aspect ratio (via CELL_ASPECT_RATIO) instead of using
    height (the flat ITERM_IMG_HEIGHT/ITERM_IMG_HEIGHT_TALL default --
    see list_target()) as-is, so e.g. a landscape photo doesn't end up
    letterboxed (extra blank space) inside a taller-than-needed box the
    way it would if every thumbnail used the same flat height
    regardless of its own shape. For every other format in
    IMAGE_EXTENSIONS, or if the file couldn't be parsed, height is used
    unchanged.

    Either way, the height actually used is then capped to
    get_terminal_height() (see its own docstring for why). The caller
    doesn't need to know what height ends up being used -- unlike an
    earlier version of this function, which returned it so callers
    could position a name printed alongside the image with cursor-
    position arithmetic that depended on knowing the image's own row
    count. _build_image_prefixes() instead prints the name (or, for -l,
    the whole permissions/owner/size/date/name line) *before* the
    image, then returns to the start of that same line with a literal
    carriage return before drawing the image over the blank space
    reserved for it there -- self-positioning, using only the image's
    own declared width, without needing its height at all.

    Returns "" if the file isn't an image or Office document (see
    QL_EXTENSIONS), or can't be read/previewed (the caller is
    expected to have already checked preconditions like
    iterm2_supported()).
    """
    ext = os.path.splitext(path)[1].lower()
    # A "~$name.docx"-style lock file Word/Excel/PowerPoint leaves next
    # to a document while it's open elsewhere isn't actually an Office
    # Open XML package (just a small owner-info stub with the same
    # extension) -- qlmanage has been observed to hang well past its
    # own timeout trying to preview one, so these are excluded from
    # is_ql entirely rather than left to fail slowly.
    is_ql = ext in QL_EXTENSIONS and not os.path.basename(path).startswith("~$")
    if ext not in IMAGE_EXTENSIONS and not is_ql:
        return ""

    max_px = max(SIPS_TARGET_PX_MIN, width * SIPS_TARGET_PX_PER_CELL)

    if is_ql:
        # No "send the original file" fallback makes sense here (an
        # OSC 1337 client can't render a .docx), so --no-sips -- which
        # exists to compare against not shrinking an image at all --
        # just disables Office thumbnails outright instead, and any
        # qlmanage/sips failure means no thumbnail for this entry.
        if no_sips:
            return ""
        data = _qlmanage_thumbnail(path, max_px)
        if not data:
            return ""
        ext = ".jpg"
    else:
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            return ""
        if not data:
            return ""

        if not no_sips and len(data) > SIPS_RESIZE_THRESHOLD_BYTES and ext not in SIPS_RESIZE_SKIP_EXTENSIONS:
            shrunk = _sips_shrink_image(data, ext, max_px)
            if shrunk:
                data = shrunk
                ext = ".jpg"

    pixel_size = get_image_pixel_size(data, ext)
    if pixel_size:
        px_width, px_height = pixel_size
        if px_width > 0 and px_height > 0:
            aspect_height = max(1, round(width * (px_height / px_width) / CELL_ASPECT_RATIO))
            height = aspect_height if allow_taller else min(aspect_height, height)

    # A thumbnail taller than the terminal forces it to scroll partway
    # through drawing, which has been observed (on a real iTerm2
    # session) to corrupt the image and misplace whatever's printed
    # after it -- so height is capped here regardless of how it was
    # arrived at (the flat --scale default above, or the aspect-ratio
    # computation just above).
    height = min(height, get_terminal_height())

    encoded = base64.b64encode(data).decode("ascii")
    name_b64 = base64.b64encode(
        os.path.basename(path).encode("utf-8", "surrogateescape")
    ).decode("ascii")
    params = ";".join(
        [
            "inline=1",
            f"width={width}",
            f"height={height}",
            "preserveAspectRatio=1",
            f"size={len(data)}",
            f"name={name_b64}",
        ]
    )
    return f"\033]1337;File={params}:{encoded}\a"


def build_hyperlink(path, text):
    """Wraps text in an OSC 8 hyperlink escape sequence pointing at
    path's file:// URL, so terminals that support OSC 8 (iTerm2, and
    others) let the user open it by clicking -- in iTerm2 specifically,
    Cmd-click on a file:// link reveals/opens the target in Finder via
    Semantic History. path is resolved to an absolute path first, since
    file:// URLs aren't meaningful relative to a cwd. Terminals without
    OSC 8 support ignore the escape sequences and just display text.
    Doesn't add any display width -- callers don't need to adjust column
    alignment for it.

    Returns the wrapped string.
    """
    url = "file://" + urllib.parse.quote(os.path.abspath(path))
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def get_display_tag_info(path, tag_mode):
    """Returns (tagnums, bg_num, dot_tagnums, all_tags) for path.
    tag_mode is opts.tag ("bg", "dot", "str", or "off" -- see --tag).
    tagnums: the Finder tag color numbers, in assignment order (see
    get_finder_tag_nums()); empty if there are none. Tags with no color
    assigned don't contribute a number here.
    bg_num: the tag number to use as the entry's background -- the last
    tag, if tag_mode == "bg"; otherwise None ("dot" always prefers a
    dot instead, "str" always prefers the text label built by
    build_tag_label(), "off" never shows a tag in any form).
    dot_tagnums: the tags to render as small dots after the name (see
    build_colored_name) -- every tag except the one used as background
    when tag_mode == "bg", every tag when tag_mode == "dot" (since none
    of them became the background), or none at all when tag_mode is
    "str" (build_tag_label()'s text label is used instead) or "off".
    all_tags: every Finder tag as (name, color_num) pairs (see
    get_finder_tags()), in assignment order, including tags with no
    color -- used by --tag=str (see build_tag_label()), which shows
    every tag's name regardless of whether it has a color.
    """
    all_tags = []
    # xattr can block trying to open sockets/FIFOs/devices/etc., so only
    # query Finder tags for regular files, directories, and symlinks,
    # which are the entry types that can actually carry them.
    if os.path.isfile(path) or os.path.isdir(path) or os.path.islink(path):
        all_tags = get_finder_tags(path)
    tagnums = [num for _, num in all_tags if num != 0]
    if not tagnums or tag_mode in ("str", "off"):
        return tagnums, None, [], all_tags
    if tag_mode == "dot":
        return tagnums, None, tagnums, all_tags
    return tagnums, tagnums[-1], tagnums[:-1], all_tags


def dot_extra_width(dot_tagnums):
    """Returns the display width added by build_colored_name's tag-dot
    rendering for dot_tagnums (a leading space plus one cell per dot, or
    0 if empty)."""
    return len(dot_tagnums) + 1 if dot_tagnums else 0


def build_tag_label(all_tags, use_color, use_truecolor, tag_colors, bg_part=None):
    """Builds the --tag display for all_tags (see get_display_tag_info()):
    a leading space followed by every Finder tag name for the entry, in
    assignment order, comma-separated inside brackets (e.g.
    " [Work, Urgent]"). A tag with a color (color_num != 0) has its name
    colored with that tag's own color (finder_sgr()), same as the
    Finder's own hue for that tag, regardless of whether that color is
    also being used as the entry's background or a dot elsewhere; a tag
    with no color assigned is left in the terminal's default foreground
    color. Returns ("", 0) if all_tags is empty. With use_color False,
    the names are plain (no color codes), same as -F's suffix or
    --quote's quoting, which likewise aren't color features.
    bg_part, if given (a "48;..." SGR parameter string), is painted
    behind the whole label -- brackets, comma separators, and leading
    space included, not just the tag names -- so a striped column's tint
    (see build_colored_name()'s stripe_column) reads as one unbroken
    block instead of leaving a colorless gap where the label sits. With
    bg_part None, those literal characters are left uncolored, as before.
    Returns (label, extra_width): extra_width is label's added display
    width, for column-layout callers that need to reserve space for it
    (see compute_multi_column_layout()).
    """
    if not all_tags:
        return "", 0
    names = [sanitize_display_name(name) for name, _ in all_tags]
    plain_label = " [" + ", ".join(names) + "]"
    if not use_color:
        return plain_label, display_width(plain_label)

    def lit(s):
        return f"\033[{bg_part}m{s}\033[0m" if bg_part else s

    colored_names = []
    for (_, num), disp in zip(all_tags, names):
        if num != 0:
            sgr = finder_sgr(num, "38", use_truecolor, tag_colors)
            span_sgr = f"{sgr};{bg_part}" if bg_part else sgr
            colored_names.append(f"\033[{span_sgr}m{disp}\033[0m")
        elif bg_part:
            colored_names.append(f"\033[{bg_part}m{disp}\033[0m")
        else:
            colored_names.append(disp)
    colored_label = lit(" [") + lit(", ").join(colored_names) + lit("]")
    return colored_label, display_width(plain_label)


def build_colored_name(name, mtime, now, use_color, bold, suffix, theme, use_truecolor, tag_colors, bg_num, dot_tagnums, stripe=False, stripe_col=None, suffix_color="off", fg_mode="date", base_fg=None):
    """Builds the colored display for name.
    foreground: a gradient color based on recency of modification
    (date_color_rgb), using the dark- or light-background stops per
    theme, or (see --base-fg) base_fg's own interpolated stops if
    base_fg is given. fg_mode="off" (see --fg-mode) disables this,
    leaving name in the terminal's default foreground color --
    background coloring (Finder tag/stripe) is unaffected either way.
    background: bg_num (see get_display_tag_info()) if set. Otherwise,
    if stripe (see --stripe) and stripe_col is set, a subtle gray tint
    alternated by column parity (see STRIPE_BG_RGB) -- with --tag=bg, a
    Finder tag background takes priority over striping when present
    (bg_num already reflects that, see get_display_tag_info()); with
    --tag=dot/str, a Finder tag never becomes the background at all
    (bg_num is always None; the tag still shows as a dot or text label),
    so this is always the one painting the entry. If neither applies,
    no background color is set. stripe_col should be None when the
    entry isn't part of a
    multi-column grid (striping by column has no meaning for -l or
    single-column output).
    Only colors name itself; render_multi_column_layout() separately
    extends a stripe column's tint across the padding after name, so the
    whole column reads as one solid-colored block (using this same
    color for consistency, or the Finder tag's color for name here if
    one applies -- the two sit side by side in that case).
    dot_tagnums are appended after name as tightly packed dots (●),
    walking backwards from the last to the first. In a striped column,
    the single space between name and the first dot, and each dot's own
    background, all get the stripe tint too (a dot's own SGR span only
    ever sets its foreground otherwise) -- without this they'd show as
    plain, uncolored gaps breaking up the striped block.
    use_truecolor selects between 24-bit truecolor and ANSI 256-color
    SGR sequences (see fg_sgr()/finder_sgr()). tag_colors ("vivid" or
    "pastel") selects the Finder tag color palette in truecolor mode
    (see --tag-colors).
    suffix_color ("off" or "type", see --suffix-color) controls
    suffix's own color: "off" (the default) leaves it inside name's
    SGR span, so it takes on the same color as the name (the recency
    gradient, or a Finder tag/stripe background). "type" instead gives
    it its own foreground color keyed by which character it is (see
    SUFFIX_TYPE_SGR), matching /bin/ls -G's default per-type colors --
    name's own foreground is unaffected either way, but any Finder tag
    or stripe background still carries over to suffix's own span, so
    the two sit side by side against the same background rather than
    the background dropping out right where suffix starts.
    Returns: (colored string, extra display width added)
    """
    if not use_color:
        # suffix (-F's type indicator) isn't a color feature and must
        # still show; dot_tagnums is safe to drop here since callers
        # only ever populate it when use_color is true in the first
        # place (it exists purely to convey Finder tag colors).
        return name + suffix, 0

    # Switch the foreground color family (cyan/magenta) based on bg_num
    # so it doesn't clash in hue with the background. Striping doesn't
    # affect this -- the gray tint doesn't clash with either family.
    # fg_mode="off" (see --fg-mode) skips this entirely, leaving name in
    # the terminal's default foreground color.
    fg_rgb = date_color_rgb(mtime, now, bg_num, theme, base_fg) if fg_mode == "date" else None

    stripe_column = stripe and stripe_col is not None
    stripe_alt = stripe_col is not None and stripe_col % 2 == 0
    use_stripe = bg_num is None and stripe_column

    bg_part = None
    if bg_num is not None:
        bg_part = finder_sgr(bg_num, "48", use_truecolor, tag_colors)
    elif use_stripe:
        bg_part = stripe_sgr(use_truecolor, theme, stripe_alt)

    parts = []
    if bold:
        parts.append("1")
    if fg_rgb:
        parts.append(fg_sgr(fg_rgb, use_truecolor))
    if bg_part:
        parts.append(bg_part)

    suffix_type_sgr = SUFFIX_TYPE_SGR.get(suffix) if suffix_color == "type" else None
    # A Finder tag or stripe background carries over to suffix's own SGR
    # span too (alongside its type color) -- otherwise the background
    # would drop out right where suffix starts, breaking a striped
    # column's solid-colored block or a Finder tag cell's background.
    suffix_sgr = f"{suffix_type_sgr};{bg_part}" if suffix_type_sgr and bg_part else suffix_type_sgr

    if parts:
        sgr = ";".join(parts)
        if suffix_sgr:
            out = f"\033[{sgr}m{name}\033[0m\033[{suffix_sgr}m{suffix}\033[0m"
        else:
            out = f"\033[{sgr}m{name}{suffix}\033[0m"
    elif suffix_sgr:
        out = f"{name}\033[{suffix_sgr}m{suffix}\033[0m"
    else:
        out = name + suffix

    # In a striped column, each dot's background gets the stripe tint
    # too (alongside its own foreground tag color), same reasoning as
    # the connecting space below: a dot's SGR span otherwise only ever
    # sets foreground, leaving its background to fall through to
    # whatever's behind it in the terminal rather than the stripe.
    dot_sgr_suffix = f";{stripe_sgr(use_truecolor, theme, stripe_alt)}" if stripe_column else ""

    extra = 0
    for o in reversed(dot_tagnums):
        if extra == 0:
            # This space sits between the name and the dots -- it's not
            # part of either's own color, so it's the one place a
            # striped column's tint has to be added explicitly rather
            # than inheriting it from name's own SGR span.
            if stripe_column:
                out += f"\033[{stripe_sgr(use_truecolor, theme, stripe_alt)}m \033[0m"
            else:
                out += " "
            extra = 1
        out += f"\033[{finder_sgr(o, '38', use_truecolor, tag_colors)}{dot_sgr_suffix}m●\033[0m"
        extra += 1

    return out, extra


def splice_colored_name(name, line, colored, surround_sgr=None):
    """Replaces the trailing name in a line of ls -l output (line) with
    colored. Also handles the symlink "name -> target" form. Returns
    line unchanged if neither matches.

    surround_sgr, if given, wraps everything OTHER than colored (the
    permissions/owner/size/date part, and the " -> target" part for a
    symlink) in that SGR code -- used for --stripe's row
    striping in -l, so the whole line reads as one solid-colored band
    rather than just the name. colored is left alone: it manages its
    own color already (Finder tag or stripe, from build_colored_name()),
    and nesting a second background under/over it would fight with its
    own reset.
    """
    def wrap(s):
        if not s or surround_sgr is None:
            return s
        return f"\033[{surround_sgr}m{s}\033[0m"

    n = len(name)
    if len(line) >= n and line[-n:] == name:
        return wrap(line[: len(line) - n]) + colored

    marker = name + " -> "
    last = -1
    search_from = 0
    while True:
        p = line.find(marker, search_from)
        if p == -1:
            break
        last = p
        search_from = p + 1
    if last != -1:
        prefix = line[:last]
        rest_after_name = line[last + n :]
        return wrap(prefix) + colored + wrap(rest_after_name)

    return wrap(line)


def run_ls(flags, ls_flags, paths):
    """Shells out to real ls(1) with flags + ls_flags + paths and
    returns its stdout as a list of lines (no trailing empty line)."""
    cmd = ["ls"] + flags + ls_flags + ["--"] + list(paths)
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    text = result.stdout.decode("utf-8", errors="surrogateescape")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def get_terminal_width():
    """Returns the terminal width to lay out multi-column output for:
    the actual terminal width if stdout is a tty, else the COLUMNS
    environment variable, else 80."""
    width = None
    try:
        width = os.get_terminal_size(sys.stdout.fileno()).columns
    except OSError:
        width = None
    if not width or width <= 0:
        try:
            width = int(os.environ.get("COLUMNS", ""))
        except ValueError:
            width = None
    if not width or width <= 0:
        width = 80
    return width


def get_terminal_height():
    """Returns the terminal height, the same way get_terminal_width()
    gets its width (falling back to the LINES environment variable,
    then 24). Used by build_image_prefix() to cap a thumbnail's row
    count -- an image taller than the terminal forces it to scroll
    partway through drawing, which has been observed (on a real iTerm2
    session) to corrupt the image and misplace whatever's printed after
    it, rather than just needing the viewer to scroll to see the rest."""
    height = None
    try:
        height = os.get_terminal_size(sys.stdout.fileno()).lines
    except OSError:
        height = None
    if not height or height <= 0:
        try:
            height = int(os.environ.get("LINES", ""))
        except ValueError:
            height = None
    if not height or height <= 0:
        height = 24
    return height


# Sentinel for a compact-mode grid slot claimed by an earlier column's
# spanning entry (see compute_multi_column_layout()'s build_grid()) --
# distinct from None, a slot with nothing in it at all (e.g. the grid's
# last column short of entries), which render_multi_column_layout()
# still paints for a striped column (see stripe_active_cell()) even
# though nothing is actually there.
BLOCKED = object()


def compute_multi_column_layout(namelen, plainlen, opt_f, opt_columns, width, stripe=False):
    """Computes the down-then-across grid layout (columns filled
    top-to-bottom, left column first, exactly like plain ls -C) from
    entry widths alone, without needing the final colored strings. This
    lets callers learn each entry's starting column (e.g. for --stripe)
    before building those strings, then hand the same layout to
    render_multi_column_layout() once they're ready.

    stripe must match what will be passed to render_multi_column_layout()
    for this layout: with stripe True, render_multi_column_layout() pads
    a row's last entry to its full column width whenever that column is
    striped (see its docstring), instead of leaving it un-padded like a
    non-striped listing does -- the fit check below has to reserve that
    same width, or a row that looks like it fits can still overflow once
    rendered.

    opt_columns selects the layout mode:

    "classic": plain ls -C -- column width is fixed at the longest name
    across every entry, so a single very long name widens every column
    and can collapse the whole listing toward one column.

    "compact" (the default): column width is normally the same as
    classic, but an entry whose width is more than double the "typical"
    column width (one computed after setting such outliers aside) is
    treated as long: instead of stretching every column to fit it, it
    spans multiple column slots (rounded up), occupying that same row's
    worth of slots in the following column(s) too. Those following
    columns simply skip that one row -- the entry that would have landed
    there is pushed down to the column's next unclaimed row -- rather
    than every later cell on the row shifting sideways out of alignment.
    This keeps unrelated columns/rows compact instead of collapsing the
    whole listing toward a single column. If this doesn't actually let
    compact fit more columns than classic would (e.g. no name is long
    enough to matter), the classic layout is used instead -- same
    information, without the skipped-cell gaps spanning entries leave in
    their wake for no benefit.

    Returns a dict with at least "mode" and "col_of_idx" (a list, length
    n, mapping each entry index to its starting column); the rest of the
    dict is mode-specific, opaque to callers other than
    render_multi_column_layout().
    """
    n = len(namelen)
    if n == 0:
        return {"mode": "empty", "col_of_idx": []}
    if n == 1:
        return {"mode": "single", "col_of_idx": [0]}

    def compute_classic(rows_width):
        """Plain ls -C: column width is fixed at the longest name across
        every entry. (Algorithm verified against real ls -CG/-CGF
        output.) Returns (rows, cols, colwidth)."""
        colwidth = max(namelen) + 1
        if opt_f:
            colwidth += 1

        # The column count isn't simply width // colwidth; instead, rows
        # are increased from 1 until ceil(n/rows) columns fit within
        # width (verified against real ls -C output). If nothing fits
        # (e.g. colwidth alone exceeds width), falls back to a single
        # column, not a single (very wide) row.
        rows, cols = n, 1
        for candidate_rows in range(1, n + 1):
            candidate_cols = (n + candidate_rows - 1) // candidate_rows
            if candidate_cols * colwidth <= rows_width:
                rows, cols = candidate_rows, candidate_cols
                break
        return rows, cols, colwidth

    def classic_layout():
        rows, cols, colwidth = compute_classic(width)
        col_of_idx = [idx // rows for idx in range(n)]
        return {
            "mode": "classic",
            "rows": rows,
            "cols": cols,
            "colwidth": colwidth,
            "col_of_idx": col_of_idx,
        }

    if opt_columns == "classic":
        return classic_layout()

    extra_f = 1 if opt_f else 0
    cellwidth = [namelen[i] + 1 + extra_f for i in range(n)]

    # Determine the "typical" column width by setting aside entries more
    # than double the median cell width, then use the max of what's left.
    # Those set-aside entries are the ones treated as long/spanning below.
    sorted_cw = sorted(cellwidth)
    median_cw = sorted_cw[len(sorted_cw) // 2]
    long_threshold = median_cw * 2
    normal_cw = [w for w in cellwidth if w <= long_threshold]
    base_colwidth = max(normal_cw) if normal_cw else max(cellwidth)

    # How many column slots (rounded up) each entry occupies, and the
    # resulting reserved width. Normal entries always occupy exactly 1.
    span = [-(-cellwidth[i] // base_colwidth) for i in range(n)]
    occupied = [span[i] * base_colwidth for i in range(n)]

    def build_grid(rows):
        """Fills columns top-to-bottom, left to right, taking entries in
        order. A spanning entry claims its row in the next span-1
        column(s) too (recorded in blocked_next), so those columns leave
        that row empty and resume with their next entry one row lower.
        Returns the list of columns; each column is a list of length
        rows holding an index into final, BLOCKED for a slot claimed by
        an earlier column's span (already rendered there -- nothing
        belongs here), or None for a slot with nothing in it at all
        (e.g. the last column short of entries -- see
        stripe_active_cell()). Columns keep being emitted -- even once
        every entry has been placed -- for as long as a pending span
        still reserves one, so the grid's width always reflects every
        entry's full occupied width, not just however many entries were
        left to place it.
        """
        columns = []
        blocked_next = {}
        idx = 0
        c = 0
        while idx < n or blocked_next:
            col = [None] * rows
            blocked_here = blocked_next.pop(c, set())
            for br in blocked_here:
                col[br] = BLOCKED
            r = 0
            while r < rows and idx < n:
                if r in blocked_here:
                    r += 1
                    continue
                col[r] = idx
                s = span[idx]
                for k in range(1, s):
                    blocked_next.setdefault(c + k, set()).add(r)
                idx += 1
                r += 1
            columns.append(col)
            c += 1
        return columns

    # Same idea as plain ls -C: rows are increased from 1 until the
    # number of columns needed to place every entry fits within width.
    # Spanning entries can make more columns necessary than plain
    # ceil(n/rows) would, since the rows/columns they claim in their
    # neighbors go unused rather than being backfilled. The fit check
    # mirrors render_multi_column_layout()'s rule exactly (every entry
    # but the row's last reserves its full occupied width) rather than a
    # coarse len(grid)*base_colwidth estimate, which undercounts when a
    # spanning entry ends up alone in the grid's last column (see
    # build_grid(): its reserved trailing columns exist, but they're
    # empty on every row, so simply multiplying column count by
    # base_colwidth overstates how much space normal columns need while
    # understating what a lone trailing spanning entry actually renders
    # at -- its un-padded width can still exceed one base_colwidth).
    #
    # One exception: if a row's last entry is wider than width all by
    # itself, no choice of rows/columns can make that row fit -- same as
    # an overlong word in wrapped text -- so that entry's own width is
    # left out of ITS row's check (the rest of the row still has to
    # fit). Without this, a single such entry (typically the sorted
    # list's last one, always ending up last-in-row) would make every
    # candidate fail and collapse the whole listing to one column.
    #
    # With stripe True, a row's last entry needs its full occupied
    # width counted (not its un-padded raw width), since every column is
    # striped, matching render_multi_column_layout()'s own last-in-row
    # exception for striping (see its docstring) -- otherwise this check
    # underestimates the row and a stripe-filled last column can
    # overflow width once actually rendered.
    #
    # Also with stripe True: a slot with nothing in it at all
    # (None, not BLOCKED -- see build_grid()) still gets painted, since
    # every column is striped (see render_multi_column_layout()'s
    # stripe_active_cell()), reserving a full base_colwidth of width
    # where before there was nothing to account for -- so it has to be
    # counted here too, or a row that looks like it fits can overflow
    # once actually rendered (the same class of bug as the last-entry
    # exception above).
    #
    # "Last" here means the rightmost column any row ever has real
    # content in (effective_last_column() below) -- a fixed property of
    # the whole grid, not of any one row. An earlier column doesn't
    # become "last" just because this particular row happens to have
    # nothing past it (e.g. a short striped column, or an unstriped one
    # with nothing on this row): render_multi_column_layout() always
    # reserves that column's separator gap regardless, so every row's
    # right edge for a given column lines up instead of jittering by a
    # character depending on what that row happens to contain.
    stripe_active = stripe

    def effective_last_column(grid):
        for c in range(len(grid) - 1, -1, -1):
            if any(isinstance(v, int) for v in grid[c]):
                return c
        return 0

    def grid_fits(grid, rows):
        effective_last = effective_last_column(grid)
        for r in range(rows):
            total = 0
            for c, col in enumerate(grid):
                v = col[r]
                if isinstance(v, int):
                    is_last = c + span[v] - 1 >= effective_last
                    w = cellwidth[v] if (is_last and not stripe_active) else occupied[v]
                elif v is None and stripe_active and any(isinstance(x, int) for x in col):
                    w = base_colwidth
                else:
                    continue
                if w <= width:
                    total += w
                # else: unavoidable overflow from this one cell alone --
                # same as an overlong word in wrapped text -- so it's
                # left out of the budget; the rest of the row still has
                # to fit.
            if total > width:
                return False
        return True

    def last_real_column_count(grid):
        """Returns the number of entries in the rightmost column that
        actually holds any (skips wholly-blocked trailing columns --
        see build_grid()).
        Used to reject candidates whose last column is left mostly
        empty: the smallest-rows-that-fits search below can otherwise
        settle on a rows count where 3 out of 4 columns are full and the
        4th only has a couple of entries (down-then-across dumps
        whatever's left over into the last column), which reads as
        obviously lopsided rather than an intentional layout choice.
        """
        for col in reversed(grid):
            count = sum(1 for v in col if isinstance(v, int))
            if count > 0:
                return count
        return 0

    # A spanning entry's own column is decided purely by its position in
    # the (already-sorted) listing -- idx // candidate_rows -- so
    # reversing the sort order can shift where it lands relative to
    # other real content on its row, which changes which candidate_rows
    # values grid_fits() accepts. In the worst case (e.g. a couple of
    # very wide names ending up a few slots from the end of the
    # listing), NO candidate_rows short of n satisfies
    # last_real_column_count's density check, even though a smaller,
    # merely lopsided candidate_rows already fits width constraints --
    # lopsided beats the trivial rows=n/one-column case, so it's tried
    # first (candidate_rows == n is excluded from this search since it
    # always trivially satisfies both checks -- everything lands in one
    # real column -- and would otherwise always win the loop before this
    # fallback is even considered).
    rows = n
    grid = build_grid(n)
    fallback_rows, fallback_grid = None, None
    for candidate_rows in range(1, n):
        candidate_grid = build_grid(candidate_rows)
        if not grid_fits(candidate_grid, candidate_rows):
            continue
        if fallback_rows is None:
            fallback_rows, fallback_grid = candidate_rows, candidate_grid
        if last_real_column_count(candidate_grid) >= max(1, candidate_rows // 2):
            rows, grid = candidate_rows, candidate_grid
            break
    else:
        if fallback_rows is not None:
            rows, grid = fallback_rows, fallback_grid

    # compact's entire point is fitting more columns than classic would
    # by letting long names spread across slots instead of widening
    # every column; if it doesn't actually beat classic's column count
    # here (e.g. no entry is long enough to matter), classic reads
    # better -- same information, without the skipped cells spanning
    # entries leave behind. Compare against classic's real column count,
    # not compact's grid length, since build_grid() can end with
    # wholly-empty trailing columns (see its docstring).
    compact_cols = sum(1 for col in grid if any(isinstance(v, int) for v in col))
    _, classic_cols, _ = compute_classic(width)
    if compact_cols <= classic_cols:
        return classic_layout()

    col_of_idx = [0] * n
    for c, col in enumerate(grid):
        for idxval in col:
            if isinstance(idxval, int):
                col_of_idx[idxval] = c

    return {
        "mode": "compact",
        "rows": rows,
        "grid": grid,
        "occupied": occupied,
        "base_colwidth": base_colwidth,
        "col_of_idx": col_of_idx,
        "effective_last_col": effective_last_column(grid),
    }


def render_multi_column_layout(layout, final, plainlen, stripe=False, theme="light", use_truecolor=False, hang_width=0):
    """Renders final (colored entry strings) into lines, arranged per
    layout (from compute_multi_column_layout()).

    With stripe True, the padding after each entry (up to the
    column's full width, minus the trailing separator space -- see
    below) is filled with the same per-column tint as build_colored_name()
    applies to the entry itself (see STRIPE_BG_RGB/STRIPE_BG_CODE) --
    every column, alternating color by parity, so the whole column reads
    as one solid-colored block rather than just the name glyphs. This
    applies even to the last entry in a row (normally left unpadded),
    since here the point is to paint the column, not just
    line up the next one. An entry with a Finder tag background keeps
    that color for its own name (see build_colored_name()); only the
    padding after it picks up the column's stripe tint, so the two
    colors sit side by side in that cell.

    The last character of that padding -- the separator space
    immediately before the next column starts -- is left unpainted, so
    adjacent stripe blocks read as visually distinct columns rather than
    merging into one solid band. That's skipped only for a column at or
    past effective_last_column() (a fixed property of the whole grid,
    not of any one row -- see compute_multi_column_layout()): there's
    truly no next column ever, on any row, to separate from, so it's
    fully painted right up to the edge instead (this matters most for a
    spanning entry, which can otherwise fall a visually noticeable step
    short of the boundary it was reserved up to). A column short of
    effective_last_column() always reserves its gap regardless of what
    this particular row happens to contain past it, so a given column's
    right edge lines up the same way on every row it appears in, rather
    than jittering by a character depending on the row.

    hang_width is the width of the unquoted-name hanging-indent space
    (see _build_entries()'s hang_prefix) when --quote is active and at
    least one name in the listing needed quoting -- 0 otherwise. A real
    entry already carries its own hang_prefix as part of its rendered
    text, so it's excluded from that entry's own padding automatically.
    A wholly empty cell (idx is None -- nothing on that row in that
    column) has no such text to carry it, so without this, its stripe
    paint would start hang_width characters further left than every
    other row of that same column that does have an entry, leaving a
    ragged notch in what should read as one straight-edged block.
    Leaving that same leading sliver unpainted here keeps the column's
    left edge consistent across every row.

    Returns the list of rendered output lines.
    """
    mode = layout["mode"]
    if mode == "empty":
        return []
    if mode == "single":
        return [final[0]]

    stripe_active = stripe

    def padding(width, c, row_end=False, hang=0):
        if width <= 0:
            return ""
        if stripe_active:
            lead = ""
            if hang > 0 and hang < width:
                lead = " " * hang
                width -= hang
            stripe_pad_sgr = stripe_sgr(use_truecolor, theme, c % 2 == 0)
            if row_end:
                # Nothing follows on this line, so there's no next
                # column to leave a separating gap before -- paint the
                # whole thing, right up to the edge of the last column
                # this entry occupies.
                return f"{lead}\033[{stripe_pad_sgr}m{' ' * width}\033[0m"
            # Leave the final space (the gap before the next column)
            # unpainted, rather than tinting the whole padding run.
            colored_width = width - 1
            if colored_width <= 0:
                return lead + " " * width
            return f"{lead}\033[{stripe_pad_sgr}m{' ' * colored_width}\033[0m "
        return " " * width

    if mode == "classic":
        n = len(final)
        rows, cols, colwidth = layout["rows"], layout["cols"], layout["colwidth"]
        lines = []
        for r in range(rows):
            # Column c*rows+r running past n means every later column
            # in this row is past n too (idx only grows with c for a
            # fixed r), so a short row's trailing gap is just this one
            # contiguous stretch. In a striped column, it still gets
            # painted -- e.g. a short last column, having fewer entries
            # than the rest -- rather than left blank; skipped entirely
            # otherwise, same as before.
            row_items = []
            for c in range(cols):
                idx = c * rows + r
                if idx < n:
                    row_items.append((c, idx))
                elif stripe_active:
                    row_items.append((c, None))
            parts = []
            for i, (c, idx) in enumerate(row_items):
                # row_is_last (nothing else on this row) decides whether
                # a plain entry skips padding entirely, same as real ls
                # -- no trailing whitespace. col_is_last -- column
                # cols-1 is always the grid's true last column (classic
                # never leaves a trailing column completely empty -- see
                # compute_multi_column_layout()) -- is a fixed property
                # of the column instead, used only for a striped
                # column's full-paint decision, so its right edge lines
                # up the same way on every row regardless of what this
                # particular row happens to contain past it.
                row_is_last = i == len(row_items) - 1
                col_is_last = c == cols - 1
                if idx is None:
                    parts.append(padding(colwidth, c, row_end=col_is_last, hang=hang_width))
                    continue
                item = final[idx]
                length = plainlen[idx]
                if row_is_last and not stripe_active:
                    parts.append(item)
                elif stripe_active:
                    parts.append(item + padding(colwidth - length, c, row_end=col_is_last))
                else:
                    parts.append(item + padding(colwidth - length, c, row_end=False))
            lines.append("".join(parts))
        return lines

    rows, grid, occupied, base_colwidth = layout["rows"], layout["grid"], layout["occupied"], layout["base_colwidth"]
    effective_last_col = layout["effective_last_col"]
    # A column that never holds a single real entry (fully None/BLOCKED
    # on every row -- a pure span-reservation artifact left behind by
    # build_grid()) shouldn't get the blank-cell treatment below: that's
    # for a column that legitimately has fewer entries than the rest
    # (e.g. the grid's last one), not a column that was never real to
    # begin with, which would otherwise paint a stray colored bar down
    # every row for no reason.
    col_has_content = [any(isinstance(v, int) for v in col) for col in grid]
    lines = []
    for r in range(rows):
        # A slot with nothing in it at all (None, not BLOCKED -- see
        # build_grid()) still gets included here when its column is
        # striped, so a short column (e.g. the grid's last one, having
        # fewer entries than the rest) still reads as part of the
        # striped band instead of leaving a gap where its tint should
        # be. A BLOCKED slot is skipped as before: it's already covered
        # by whatever span claimed it.
        row_items = [
            (c, col[r])
            for c, col in enumerate(grid)
            if isinstance(col[r], int)
            or (col[r] is None and stripe_active and col_has_content[c])
        ]
        parts = []
        for i, (c, idx) in enumerate(row_items):
            # row_is_last (nothing else on this row) decides whether a
            # plain entry skips padding entirely, same as real ls -- no
            # trailing whitespace. col_is_last -- whether this cell's
            # rightmost occupied column reaches effective_last_col, the
            # rightmost column ANY row ever has real content in, a fixed
            # property of the whole grid rather than of this one row --
            # is used only for a striped column's full-paint decision,
            # so its right edge lines up the same way across every row
            # it appears in (see effective_last_column(): this
            # particular row having nothing further right doesn't make
            # an earlier column "last").
            row_is_last = i == len(row_items) - 1
            span_here = 1 if idx is None else occupied[idx] // base_colwidth
            col_is_last = c + span_here - 1 >= effective_last_col
            if idx is None:
                parts.append(padding(base_colwidth, c, row_end=col_is_last, hang=hang_width))
                continue
            item = final[idx]
            length = plainlen[idx]
            if row_is_last and not stripe_active:
                parts.append(item)
            elif stripe_active:
                parts.append(item + padding(occupied[idx] - length, c, row_end=col_is_last))
            else:
                parts.append(item + padding(occupied[idx] - length, c, row_end=False))
        lines.append("".join(parts))
    return lines


def format_multi_column(final, namelen, plainlen, opt_f, opt_columns, stripe=False, theme="light", use_truecolor=False, hang_width=0):
    """Convenience wrapper combining compute_multi_column_layout() and
    render_multi_column_layout() for callers that don't need each
    entry's column ahead of time (see compute_multi_column_layout() for
    what opt_columns selects). Returns the list of rendered output
    lines."""
    width = get_terminal_width()
    layout = compute_multi_column_layout(namelen, plainlen, opt_f, opt_columns, width, stripe)
    return render_multi_column_layout(layout, final, plainlen, stripe, theme, use_truecolor, hang_width)


@dataclass
class Options:
    """Every option list_target() and its helpers need.

    a/A/l/h/f/one/C/i/t/d/b/r/S/X/reverse/quote/group_dirs_first/stripe
    mirror the short/boolean-long options (-a/-A/-l/-h/-F/-1/-C/-I/-t/
    -d/-B/-R/-S/-X/-r/--quote/--group-directories-first/--stripe).

    color/theme/tag_colors/columns/tag/suffix_color/fg_mode mirror the
    long mode-style options (--color/--theme/--tag-colors/--columns/
    --tag/--suffix-color/--fg-mode); parse_options() validates their
    values against each option's own choices. tag ("bg", "dot", "str",
    or "off") selects how a Finder tag is shown (see --tag); stripe is
    the separate on/off flag for the column/row background tint (see
    --stripe), independent of tag.

    base_fg mirrors --base-fg: an (r, g, b) tuple parsed from a 6-hex-
    digit RRGGBB string (see parse_hex_rgb()), or None if not given.

    scale mirrors --scale: a positive integer thumbnail size multiplier
    for -I (see ITERM_IMG_WIDTH/ITERM_IMG_HEIGHT's own comment); 1 (no
    scaling) if not given.

    use_color/use_truecolor are resolved by main() from color plus
    environment/tty detection (isatty(), CLICOLOR_FORCE, COLORFGBG,
    COLORTERM). theme starts as parse_options() left it ("light",
    "dark", or "auto") and is resolved by main() in place, replacing
    "auto" with a definite "light"/"dark" guess from
    detect_dark_background() -- every other function that takes a theme
    argument (date_color_rgb(), stripe_sgr(), etc.) expects that
    resolved value, never "auto".

    no_sips mirrors --no-sips, an undocumented/hidden flag (not in
    print_help(), macls.md, or the module docstring's own option list)
    that disables -I's sips(1)-based thumbnail shrinking -- see its own
    handling in parse_options().
    """

    a: bool = False
    A: bool = False
    l: bool = False
    h: bool = False
    f: bool = False
    one: bool = False
    C: bool = False
    i: bool = False
    t: bool = False
    d: bool = False
    b: bool = False
    r: bool = False
    S: bool = False
    X: bool = False
    reverse: bool = False
    quote: bool = False
    group_dirs_first: bool = False
    stripe: bool = False
    no_sips: bool = False
    color: str = "auto"
    theme: str = "auto"
    tag_colors: str = "pastel"
    columns: str = "compact"
    tag: str = "bg"
    suffix_color: str = "off"
    fg_mode: str = "date"
    base_fg: Optional[tuple] = None
    scale: int = 1
    use_color: bool = False
    use_truecolor: bool = False


def _build_ls_flags(opts):
    """The subset of opts that also apply to the real ls(1) invocations
    list_target() shells out to (see run_ls()).

    opts.X is deliberately never passed through here: on macOS, ls(1)'s
    own -X means "don't descend into directories that cross filesystem
    boundaries" when listing recursively -- a completely different,
    GNU-ls-only meaning from sort-by-extension. Since macls.py never
    passes -R through to ls(1) itself (see list_target()'s own
    recursion), macOS's -X would be a silent no-op here, not an error,
    so passing it along would look like it worked while doing nothing.
    -X's actual sort-by-extension behavior is applied in Python instead
    (see list_target()'s `order` computation), same as
    --group-directories-first.

    opts.reverse is passed through as ls(1)'s own -r only when opts.X
    is not set: with -X, reversal is folded into that same Python-side
    reordering instead (list_target() applies it to the whole
    extension-sorted sequence), since plain ls -r would otherwise
    reverse the wrong (pre-extension-sort) order.

    Returns the list of ls(1) flag strings.
    """
    ls_flags = []
    if opts.a:
        ls_flags.append("-a")
    elif opts.A:
        ls_flags.append("-A")
    if opts.t:
        ls_flags.append("-t")
    if opts.S:
        ls_flags.append("-S")
    if opts.reverse and not opts.X:
        ls_flags.append("-r")
    if opts.d:
        ls_flags.append("-d")
    if opts.h:
        ls_flags.append("-h")
    return ls_flags


def _extension_sort_key(name):
    """Returns -X's sort key: the text after the last '.' in the raw
    name, or "" if there is none -- matches GNU ls's cmp_extension (strrchr on
    the whole name, no special-casing for a leading dot), so a dotfile
    like ".bashrc" sorts under extension "bashrc", not "" from its own
    leading dot."""
    return name.rsplit(".", 1)[1] if "." in name else ""


def _fetch_mtimes(full_paths, use_color):
    """Returns (now, mtimes): the current time and each path's mtime,
    fetched together for coloring the foreground (modification
    recency). Skipped (mtimes all None) when use_color is False, since
    it would be wasted work."""
    if not use_color:
        return None, [None] * len(full_paths)
    now = int(time.time())
    mtimes = []
    for p in full_paths:
        try:
            # Use lstat to match stat -f %m's behavior (the symlink's
            # own mtime, not the target's).
            mtimes.append(int(os.lstat(p).st_mtime))
        except OSError:
            mtimes.append(None)
    return now, mtimes


# Cap on concurrent build_image_prefix() calls (see
# _build_images_parallel()) -- generous enough to hide sips(1)'s own
# ~200ms process-startup latency behind concurrency for a directory
# full of large images, without spawning an unbounded number of sips
# processes at once for a directory with hundreds of them.
IMAGE_THUMBNAIL_WORKERS = 8


def _build_images_parallel(full_paths, width, height, no_sips=False, allow_taller=True):
    """Returns build_image_prefix()'s result for each of full_paths, in
    the same order, computed concurrently via a thread pool.

    Each call is either a plain file read (fast) or, above
    SIPS_RESIZE_THRESHOLD_BYTES, a sips(1) subprocess whose own
    process-startup/framework-load cost (confirmed against a real
    sips invocation to be on the order of ~200ms, largely independent
    of the image's own size) would otherwise be paid once per image,
    serially, for every large image in the listing -- e.g. `-I -l
    ~/Pictures` over a folder of large photos. Since that cost is
    almost entirely spent waiting on the external sips process rather
    than on the GIL, a thread pool (not multiprocessing) is enough to
    run them concurrently. A lone image, or none at all, skips the
    pool entirely -- there's nothing to overlap.

    allow_taller is forwarded as-is to every build_image_prefix() call
    -- see its own docstring; the caller here is responsible for
    passing False in multi-column output.
    """
    non_dirs = [p for p in full_paths if os.path.isfile(p)]
    if len(non_dirs) <= 1:
        return [build_image_prefix(p, width, height, no_sips, allow_taller) if os.path.isfile(p) else "" for p in full_paths]
    with concurrent.futures.ThreadPoolExecutor(max_workers=IMAGE_THUMBNAIL_WORKERS) as pool:
        results = pool.map(
            lambda p: build_image_prefix(p, width, height, no_sips, allow_taller) if os.path.isfile(p) else "",
            full_paths,
        )
        return list(results)


def _stream_image_suffixes(full_paths, width, height, stacked_flags, no_sips=False):
    """Lazily yields each entry's img_suffix in full_paths' own order --
    the \\r/\\n-then-image string _build_image_prefixes()'s single_line
    branch would otherwise build eagerly for every entry before
    returning (see build_image_prefix(), which this still calls the
    same way, on the same bounded thread pool as
    _build_images_parallel()).

    Used only for -1/-l (single_line) mode, where each entry's own
    output line is independent of every other entry's -- so a caller
    that prints as it consumes this, rather than collecting it into a
    list first, streams each line out as soon as its own thumbnail (if
    it has one) is ready, instead of every entry in a large directory
    blocking on whichever one is slowest to shrink (see
    _sips_shrink_image()).

    concurrent.futures.Executor.map() submits every item to the pool up
    front (so all of them start making progress immediately, bounded by
    IMAGE_THUMBNAIL_WORKERS) but only blocks on -- and only yields --
    one result at a time, in submission order, as the caller consumes
    the returned iterator; entries after the one currently being
    awaited keep running in the background in the meantime. The pool
    stays open across each yield (a generator suspends, but doesn't
    exit, its `with` block) and is only torn down once every entry has
    been produced (or the generator is otherwise closed/discarded).
    """
    def compute(i_and_path):
        i, p = i_and_path
        img = build_image_prefix(p, width, height, no_sips) if os.path.isfile(p) else ""
        if not img:
            return ""
        if stacked_flags and stacked_flags[i]:
            return "\n" + img
        return "\r" + img

    with concurrent.futures.ThreadPoolExecutor(max_workers=IMAGE_THUMBNAIL_WORKERS) as pool:
        yield from pool.map(compute, enumerate(full_paths))


def _build_image_prefixes(full_paths, opt_i, width=ITERM_IMG_WIDTH, height=ITERM_IMG_HEIGHT, stacked_flags=None, single_line=False, no_sips=False):
    """-I: builds a thumbnail prefix/suffix pair for each entry.

    single_line (see list_target()'s scale_applies) must be true only
    where each entry has an entire physical terminal line to itself
    with nothing else sharing it -- -1 or -l (the only two contexts
    this is ever actually called with opt_i True in the first place,
    since -I disables itself outright on non-tty output -- see
    main()). There, every entry (whether or not it actually gets
    a thumbnail) gets img_col_pad -- blank padding `width`+1 cells wide
    -- as its prefix, so every entry's own text (the name in -1, or the
    whole permissions/owner/size/date/name line in -l) starts at the
    same column regardless of whether that particular entry ends up
    with a thumbnail. An entry with an actual thumbnail (a regular file
    with a recognized image extension -- see build_image_prefix()) then
    gets a suffix that draws it *after* that entry's own text has
    already been printed: a literal carriage return (back to the start
    of the line the text was just printed on) followed by the image
    escape sequence itself, which then draws over the blank padding the
    prefix reserved, immediately to the left of the text -- rather than
    drawing the image *before* the text and then using cursor-position
    arithmetic to fit the text in alongside it. This works for any
    image height (1 row or many -- build_image_prefix() decides that,
    scaled by --scale and, for the 4 formats whose real pixel
    dimensions can be read, further adjusted for that image's own
    aspect ratio) without this function needing to know it at all: per
    iTerm2's own inline image protocol, the cursor after drawing lands
    at the image's own bottom row, ready for the following entry's own
    output to continue there -- confirmed against a real iTerm2 session
    not to overlap the next entry even for a multi-row thumbnail.

    stacked_flags[i], when True (see list_target()'s own stacked_flags,
    computed only where single_line and --scale both apply), instead
    places that entry's thumbnail on its own line below the text (a
    newline instead of a carriage return before the image) rather than
    beside it -- used when width*scale plus that entry's own text would
    otherwise overflow the terminal's width if kept side by side.

    With single_line False (multi-column output, where several
    entries' worth of text share one physical line, and --scale never
    applies -- see list_target()), the carriage-return trick above
    isn't safe: \\r always returns to column 0 of the whole physical
    line, not to wherever this particular entry's own column started,
    so a later entry's own image would be drawn back at the start of
    the line, on top of every earlier entry sharing that row instead of
    in its own column. There, an entry with a thumbnail instead gets
    the image drawn directly as its prefix (immediately followed by one
    separator space, with no cursor tricks and no suffix at all) --
    always exactly 1 row tall in this context, since --scale doesn't
    apply, so there's no need to fit a taller thumbnail in alongside
    the text either. stacked_flags is meaningless (and ignored) here.

    Returns (img_prefixes, img_suffixes, img_col_width).

    The image itself is deliberately not wrapped in an OSC 8 hyperlink
    (unlike the name -- see build_hyperlink()): tried and confirmed
    against a real iTerm2 session not to make the thumbnail clickable,
    since OSC 1337 draws pixels directly into its cells rather than
    going through the normal per-cell text stream that OSC 8's
    hyperlink attribute rides along with.
    """
    if not opt_i:
        return [""] * len(full_paths), [""] * len(full_paths), 0
    img_col_width = width + 1
    img_col_pad = " " * img_col_width
    imgs = _build_images_parallel(full_paths, width, height, no_sips, allow_taller=single_line)
    img_prefixes = []
    img_suffixes = []
    for i, img in enumerate(imgs):
        if not single_line:
            # Multi-column output: the image must be drawn in place, as
            # part of this entry's own column -- see single_line above.
            img_prefixes.append((img + " ") if img else img_col_pad)
            img_suffixes.append("")
            continue
        img_prefixes.append(img_col_pad)
        if not img:
            img_suffixes.append("")
        elif stacked_flags and stacked_flags[i]:
            img_suffixes.append("\n" + img)
        else:
            img_suffixes.append("\r" + img)
    return img_prefixes, img_suffixes, img_col_width


def _compute_quoting(names, opt_quote, is_tty):
    """--quote: whether ANY entry in this listing needs quoting decides
    whether entries that don't get a leading space instead, so the
    opening quote of a quoted name "hangs" one column to the left of its
    unquoted neighbors rather than pushing the neighbors' own text out
    of alignment (matching GNU ls's shell quoting style, in both -C and
    -l). Requires a first pass over every name in the listing before any
    of them can be finalized.

    A name containing a control character gets ANSI-C quoting ($'...',
    see ansi_c_quote()) instead: sanitize_display_name()'s usual '?'
    replacement loses the original bytes, which defeats the point of
    --quote (a displayed name that pastes back into a shell as the real
    thing); $'...' escapes them instead, so they survive. Only applies
    when writing to a terminal -- for non-tty output the raw bytes are
    already embedded as-is in plain '...' quoting, and POSIX '...'
    preserves them literally with no escaping needed, so there's nothing
    for ansi_c_quote() to improve on there.

    Returns (sanitized_names, needs_quote, ansi_c_needed, any_quoted).
    """
    ansi_c_needed = [opt_quote and is_tty and needs_ansi_c_quoting(name) for name in names]
    sanitized_names = [
        ansi_c_quote(names[i]) if ansi_c_needed[i]
        else (sanitize_display_name(names[i]) if is_tty else names[i])
        for i in range(len(names))
    ]
    needs_quote = [
        (not ansi_c_needed[i]) and opt_quote and needs_shell_quoting(sanitized_names[i])
        for i in range(len(names))
    ]
    any_quoted = any(ansi_c_needed) or any(needs_quote)
    return sanitized_names, needs_quote, ansi_c_needed, any_quoted


def _is_directory(p):
    """Whether p is itself a directory (lstat, so a symlink to one
    doesn't count -- matches -F's own @ / -B's own bold-directory
    classification). Returns a bool."""
    try:
        return stat_module.S_ISDIR(os.lstat(p).st_mode)
    except OSError:
        return False


def _is_directory_or_symlink_to_one(p):
    """Whether p is a directory, or a symlink that resolves to one (stat,
    following symlinks; a broken symlink is not a directory) -- used only
    for --group-directories-first's classification, which (matching GNU
    ls's own --group-directories-first) groups a symlink to a directory
    with real directories, unlike -F/-B's own lstat-based classification
    (see _is_directory()). Returns a bool."""
    return os.path.isdir(p)


def _build_entries(names, full_paths, sanitized_names, needs_quote, ansi_c_needed, any_quoted, opts, img_col_width):
    """Builds the per-entry display metadata that doesn't depend on the
    entry's column, computed up front so the grid layout (and thus each
    entry's starting column, needed for --stripe) can be worked
    out before the colored strings are actually built: the final quoted
    display name and its hanging-indent prefix, the -F type suffix,
    whether the entry is a directory, Finder tag background/dot info
    (see get_display_tag_info()), and the --tag name's raw tag list (see
    build_tag_label()) -- kept as (name, color_num) pairs rather than a
    pre-built label string, since the label's own background (a striped
    column's tint, or a Finder tag color -- see _build_final_entries())
    can only be known once each entry's column is, which isn't decided
    until after this function returns. Returns (disp_names,
    hang_prefixes, suffixes, is_directories, bg_nums, dot_tagnums_list,
    entry_tags, namelen, plainlen); namelen and plainlen are identical
    here (both are pre-coloring display widths) but kept separate since
    compute_multi_column_layout()/render_multi_column_layout() use them
    for logically distinct purposes (column-fit vs. per-entry padding).
    """
    disp_names = [None] * len(names)
    hang_prefixes = [""] * len(names)
    suffixes = [None] * len(names)
    is_directories = [False] * len(names)
    bg_nums = [None] * len(names)
    dot_tagnums_list = [[] for _ in names]
    entry_tags = [None] * len(names)
    plainlen = []
    namelen = []
    for i, name in enumerate(names):
        p = full_paths[i]
        disp_name = sanitized_names[i]
        hang_prefix = ""
        if needs_quote[i]:
            disp_name = shell_quote(disp_name)
        elif ansi_c_needed[i]:
            pass  # already fully quoted and escaped by ansi_c_quote()
        elif opts.quote and any_quoted:
            # Kept separate from disp_name (rather than just
            # prepending) so it renders outside whatever color this
            # entry's own name gets -- e.g. a Finder tag background
            # shouldn't bleed onto a hanging-indent space that isn't
            # part of the name.
            hang_prefix = " "
        suffix = type_suffix(p) if opts.f else ""
        is_directory = _is_directory(p)
        bg_num, dot_tagnums, tags, tag_extra = None, [], None, 0
        if opts.tag != "off" and (opts.use_color or opts.tag == "str"):
            _, bg_num, dot_tagnums, all_tags = get_display_tag_info(p, opts.tag)
            if not opts.use_color:
                bg_num, dot_tagnums = None, []
            if opts.tag == "str":
                tags = all_tags
                # use_color=False here: the label's width doesn't depend
                # on whether/how it ends up colored (see
                # _build_final_entries()), so there's no need to build
                # the colored form just to measure it.
                _, tag_extra = build_tag_label(all_tags, False, opts.use_truecolor, opts.tag_colors)
        disp_len = len(hang_prefix) + display_width(disp_name) + len(suffix) + dot_extra_width(dot_tagnums) + tag_extra + img_col_width
        disp_names[i] = disp_name
        hang_prefixes[i] = hang_prefix
        suffixes[i] = suffix
        is_directories[i] = is_directory
        bg_nums[i] = bg_num
        dot_tagnums_list[i] = dot_tagnums
        entry_tags[i] = tags
        namelen.append(disp_len)
        plainlen.append(disp_len)
    return disp_names, hang_prefixes, suffixes, is_directories, bg_nums, dot_tagnums_list, entry_tags, namelen, plainlen


def _build_final_entries(names, full_paths, disp_names, hang_prefixes, suffixes, is_directories, bg_nums, dot_tagnums_list, entry_tags, img_prefixes, img_suffixes, mtimes, now, is_tty, opts, col_of_idx):
    """Builds the final colored (see build_colored_name()) and
    hyperlinked (see build_hyperlink()) display string for each entry.
    col_of_idx (from compute_multi_column_layout(), or None outside
    multi-column output) supplies each entry's starting column for
    --stripe striping. In -l there's no column to
    stripe by, so an entry's row index stands in for it instead, only
    passed through on odd rows (the only rows -l stripes -- must match
    _render_long_format()'s own surround_sgr condition) so
    build_colored_name() gives the name itself the same
    Finder-tag-or-stripe treatment as the rest of that row's line.
    entry_tags[i] (see build_tag_label(), --tag), if any, is turned into
    a label and appended after the hyperlink-wrapped name. Each tag name
    keeps its own color independently, but the label's background (the
    brackets/commas/spaces included) picks up the same striped-column
    tint as the connecting space before a Finder-tag dot (see
    build_colored_name()) whenever this entry sits in a striped column --
    otherwise it would leave a colorless gap partway through the column's
    painted block. Outside a striped column, the label carries no
    background of its own, same as before.
    img_suffixes[i] (see _build_image_prefixes(), --scale) is appended
    at the very end, after everything else: a carriage return (or, if
    stacked, a newline) followed by the image itself, so it draws over
    the blank padding img_prefixes[i] reserved for it, right after --
    not before -- this entry's own text has already been printed.
    Empty (no effect) for an entry with no thumbnail.
    """
    final = []
    for i, name in enumerate(names):
        if opts.stripe and col_of_idx is not None:
            stripe_col = col_of_idx[i]
        elif opts.stripe and col_of_idx is None and i % 2 == 1:
            # No column to stripe by outside multi-column output (-l,
            # -1, or non-tty/non--C single-column output), so the
            # entry's row index stands in for it instead, same as -l's
            # own odd-row striping -- see _render_long_format()'s
            # surround_sgr, which extends this same treatment across
            # the rest of -l's line (permissions through the date);
            # -1/plain output has no such extra text, so striping the
            # name itself here (via build_colored_name() below) is the
            # whole effect there.
            stripe_col = i
        else:
            stripe_col = None
        colored, _extra = build_colored_name(
            disp_names[i], mtimes[i], now, opts.use_color, opts.b and is_directories[i], suffixes[i],
            opts.theme, opts.use_truecolor, opts.tag_colors,
            bg_nums[i], dot_tagnums_list[i], opts.stripe, stripe_col, opts.suffix_color, opts.fg_mode, opts.base_fg
        )
        tag_label = ""
        if entry_tags[i]:
            stripe_alt = stripe_col is not None and stripe_col % 2 == 0
            stripe_column = opts.use_color and opts.stripe and stripe_col is not None
            bg_part = stripe_sgr(opts.use_truecolor, opts.theme, stripe_alt) if stripe_column else None
            tag_label, _ = build_tag_label(entry_tags[i], opts.use_color, opts.use_truecolor, opts.tag_colors, bg_part)
        if is_tty:
            colored = build_hyperlink(full_paths[i], colored)
        final.append(img_prefixes[i] + hang_prefixes[i] + colored + tag_label + img_suffixes[i])
    return final


def _render_long_format(names, plain_l, final, img_prefixes, opts, order=None):
    """Renders -l output: splices the colored name (see
    splice_colored_name()) into each of plain_l's real permissions/
    owner/size/date lines (a prior `ls -l` call -- see list_target(),
    which also uses plain_l's own line widths to cap --scale), striping
    odd rows' whole line when opts.stripe (see splice_colored_name()'s
    surround_sgr argument). final[i][len(
    img_prefixes[i]):] -- the part being spliced in -- already ends
    with that entry's img_suffixes[i] (see _build_final_entries()), so
    a thumbnail's own carriage-return-then-image sequence rides along
    with the splice and still lands at the very end of the rendered
    line, right after the real permissions/owner/size/date/name text.

    order, when given (opts.group_dirs_first), is the permutation
    list_target() already applied to names/full_paths to group
    directories first: order[i] is that entry's position in plain_l,
    which -- fetched separately, with no grouping of its own -- is
    still in the original, ungrouped order. Without this, line i's real
    ls -l data would be spliced onto the wrong (already-regrouped)
    name.
    """
    output = []
    li = 0
    if plain_l and plain_l[0].startswith("total "):
        output.append(plain_l[0])
        li = 1
    for i, name in enumerate(names):
        idx = li + (order[i] if order is not None else i)
        if idx >= len(plain_l):
            break
        surround_sgr = stripe_sgr(opts.use_truecolor, opts.theme) if (opts.stripe and opts.use_color and i % 2 == 1) else None
        spliced = splice_colored_name(name, plain_l[idx], final[i][len(img_prefixes[i]):], surround_sgr)
        output.append(img_prefixes[i] + spliced)
    return output


def list_target(mode, show_header, paths, opts):
    """Processes and outputs one section for a group of targets.
    mode: "dir" (list the contents of a single directory) or "files"
    (list the explicitly given files/directories themselves, same as
    real ls's behavior).
    show_header: whether to print the header ("path:"). Only meaningful
    in dir mode.
    paths: target paths. Exactly 1 in dir mode, 1 or more in files mode.
    opts: an Options instance (see its docstring for every flag/mode
    field used below).

    Returns nothing -- writes its section directly to stdout (and, for
    -R, recurses into subdirectories the same way).
    """
    output = []
    join_is_dir = mode == "dir"
    target_dir = paths[0] if join_is_dir else None

    if join_is_dir and show_header:
        output.append(f"{target_dir}:")

    ls_flags = _build_ls_flags(opts)
    names = run_ls(["-1"], ls_flags, paths)

    # Full path for each name.
    if join_is_dir:
        full_paths = [f"{target_dir}/{nm}" for nm in names]
    else:
        full_paths = list(names)

    # -X (sort by extension) and --group-directories-first are both
    # applied here in Python rather than delegated to ls(1) (see
    # _build_ls_flags()'s docstring for why -X can't be), each a stable
    # sort layered on top of whatever ls(1) already produced (name, or
    # -t/-S order) so entries within a tied group keep that relative
    # order. -X goes first so its own order is what
    # --group-directories-first preserves within the directory/
    # non-directory split; -r (opts.reverse), when -X is active, is
    # folded in right after it -- reversing the whole extension-sorted
    # sequence, same as ls -r would reverse a plain name sort -- rather
    # than being passed to ls(1) itself (which would reverse the wrong,
    # pre-extension-sort order; see _build_ls_flags()).
    #
    # order (the permutation applied, if any) is threaded through to
    # _render_long_format(), which needs it to match this new ordering
    # back up against its own separate, still ls-ordered `ls -l` call.
    order = None
    if opts.X or opts.group_dirs_first:
        order = list(range(len(names)))
        if opts.X:
            order.sort(key=lambda i: _extension_sort_key(names[i]))
            if opts.reverse:
                order.reverse()
        if opts.group_dirs_first:
            order.sort(key=lambda i: 0 if _is_directory_or_symlink_to_one(full_paths[i]) else 1)
        names = [names[i] for i in order]
        full_paths = [full_paths[i] for i in order]

    now, mtimes = _fetch_mtimes(full_paths, opts.use_color)

    # Names written directly to the terminal are only sanitized when the
    # actual output destination is a terminal (matching real ls, output
    # to a pipe/file is not sanitized).
    is_tty = sys.stdout.isatty()

    multi = (not opts.l) and (not opts.one) and (opts.C or sys.stdout.isatty())

    # Computed here (ahead of the image-prefix building below) since
    # capping --scale to the terminal width needs each name's own
    # display width.
    sanitized_names, needs_quote, ansi_c_needed, any_quoted = _compute_quoting(names, opts.quote, is_tty)

    # -l's own `ls -l` call is fetched here (rather than inside
    # _render_long_format(), which used to run it itself) whenever
    # opts.l, so its line widths are available for the --scale cap
    # below too, without running it twice.
    plain_l = run_ls(["-l"], ls_flags, paths) if opts.l else None

    # -l and -1 each print exactly one entry per physical terminal
    # line, with nothing else sharing it, so --scale (see
    # ITERM_IMG_WIDTH/ITERM_IMG_HEIGHT's own comment) applies there;
    # multi-column output shares one physical line across several
    # entries' worth of text, so --scale is ignored (capped to 1)
    # there. opts.i is already False by this point for non-tty output
    # regardless (see main()), so that case never reaches here either.
    scale_applies = opts.i and not multi
    scale = opts.scale if scale_applies else 1
    term_width = get_terminal_width()
    if scale_applies and scale > 1:
        # Even stacking an entry's thumbnail below its own text (see
        # stacked_flags below) can't help if the thumbnail alone is
        # already wider than the terminal, so scale is still capped for
        # that one case -- silently, like -I itself silently disabling
        # when the terminal doesn't support it, since this is just
        # protecting the layout, not a user mistake worth flagging.
        scale = min(scale, max(1, term_width // ITERM_IMG_WIDTH))
    img_width = ITERM_IMG_WIDTH * scale
    img_height = ITERM_IMG_HEIGHT * scale

    # Per entry, whether width*scale plus that entry's own text would
    # overflow the terminal's width if kept side by side (see
    # _build_image_prefixes()'s stacked_flags) -- if so, that entry's
    # thumbnail is instead placed on its own line below the text
    # instead of shrinking the whole listing's scale down to fit the
    # single widest entry. In -l, the image sits in front of the whole
    # permissions/owner/size/date/name line (not just the name), so
    # that entire real ls -l line is what's compared; in -1, just the
    # name (plus -F's own suffix character -- a cheap approximation
    # that ignores --quote/--tag's own extra width) is.
    stacked_flags = None
    if scale_applies and scale > 1:
        if opts.l and plain_l is not None:
            entry_lines = plain_l[1:] if plain_l and plain_l[0].startswith("total ") else plain_l

            def text_width(i):
                idx = order[i] if order is not None else i
                return display_width(entry_lines[idx]) if idx < len(entry_lines) else 0
        else:
            name_extra = 1 if opts.f else 0

            def text_width(i):
                return display_width(sanitized_names[i]) + name_extra

        stacked_flags = [(img_width + text_width(i)) > term_width for i in range(len(names))]

    if scale_applies:
        # -1/-l with -I: img_prefixes here is always the same constant
        # blank pad regardless of whether a given entry actually has a
        # thumbnail (the image itself is drawn afterward via
        # img_suffixes' own \r/\n trick -- see _build_image_prefixes()'s
        # single_line branch), so it doesn't need to wait on any
        # per-file work at all. img_suffixes is left as an all-empty
        # placeholder here and computed lazily, entry by entry, in the
        # streaming loop near the end of this function instead -- see
        # _stream_image_suffixes() -- so a slow thumbnail only delays
        # its own line, not every entry before it in the directory.
        img_col_width = img_width + 1
        img_prefixes = [" " * img_col_width] * len(full_paths)
        img_suffixes = [""] * len(full_paths)
    else:
        img_prefixes, img_suffixes, img_col_width = _build_image_prefixes(full_paths, opts.i, img_width, img_height, stacked_flags, scale_applies, opts.no_sips)

    disp_names, hang_prefixes, suffixes, is_directories, bg_nums, dot_tagnums_list, entry_tags, namelen, plainlen = _build_entries(
        names, full_paths, sanitized_names, needs_quote, ansi_c_needed, any_quoted, opts, img_col_width
    )

    # --stripe's column/row painting (see render_multi_column_layout())
    # is a color feature like everything else build_colored_name()
    # draws -- without this, it would still emit SGR sequences to
    # pad/tint columns even with use_color False (e.g. piping to a
    # pager without --color=always), since opts.stripe alone otherwise
    # decides whether to stripe.
    effective_stripe = opts.stripe and opts.use_color

    # Only multi-column output has a notion of "column" to stripe by;
    # for -l/-1/non-tty output, col_of_idx stays None and
    # _build_final_entries() falls back to striping by row instead.
    layout = None
    col_of_idx = None
    if multi:
        layout = compute_multi_column_layout(namelen, plainlen, opts.f, opts.columns, get_terminal_width(), effective_stripe)
        col_of_idx = layout["col_of_idx"]

    final = _build_final_entries(
        names, full_paths, disp_names, hang_prefixes, suffixes, is_directories, bg_nums, dot_tagnums_list, entry_tags,
        img_prefixes, img_suffixes, mtimes, now, is_tty, opts, col_of_idx
    )

    if opts.l:
        lines = _render_long_format(names, plain_l, final, img_prefixes, opts, order)
    elif multi and final:
        hang_width = 1 if (opts.quote and any_quoted) else 0
        lines = render_multi_column_layout(layout, final, plainlen, effective_stripe, opts.theme, opts.use_truecolor, hang_width)
    else:
        lines = final

    if scale_applies:
        # Stream: every line built above already ends with its
        # placeholder empty img_suffix (see the scale_applies branch
        # earlier in this function), so none of it actually depends on
        # any image work having finished. Print the header/"total" line
        # (if any) immediately, then each entry's own line as soon as
        # its thumbnail (if it has one) is ready, instead of blocking
        # on every thumbnail in the directory before printing anything
        # -- see _stream_image_suffixes().
        has_total = bool(plain_l) and plain_l[0].startswith("total ")
        header_lines = lines[:1] if has_total else []
        entry_lines = lines[1:] if has_total else lines
        n_entries = len(entry_lines)
        output.extend(header_lines)
        if output:
            sys.stdout.write("\n".join(output) + "\n")
            sys.stdout.flush()
        stacked = stacked_flags[:n_entries] if stacked_flags else None
        suffixes_stream = _stream_image_suffixes(full_paths[:n_entries], img_width, img_height, stacked, opts.no_sips)
        for line, suffix in zip(entry_lines, suffixes_stream):
            sys.stdout.write(line + suffix + "\n")
            sys.stdout.flush()
    else:
        output.extend(lines)
        if output:
            sys.stdout.write("\n".join(output) + "\n")

    # -R: after this directory's own contents, recurse into each of its
    # subdirectories in the same order they were just listed (depth
    # first, matching real ls -R), skipping "." and ".." (present only
    # under -a) to avoid recursing forever. is_directories comes from
    # lstat, so a symlink to a directory is left alone here too, same as
    # real ls -R's default of not following symlinks.
    if join_is_dir and opts.r and not opts.d:
        for i, name in enumerate(names):
            if name in (".", ".."):
                continue
            if not is_directories[i]:
                continue
            print()
            list_target("dir", True, [full_paths[i]], opts)


def print_help():
    print(f"""Usage: {PROG} [-a] [-A] [-l] [-h] [-1] [-C] [-F] [-I] [--scale=n] [-t] [-S] [-X] [-r] [-d] [-R] [-B] [--color=when] [--theme=mode] [--tag-colors=mode] [--columns=mode] [--tag=mode] [--stripe] [--suffix-color=mode] [--fg-mode=mode] [--base-fg=RRGGBB] [--quote] [--group-directories-first] [--version] [path...]

Options:
  -a        Show all files, including . and ..
  -A        Show all files except . and ..
  -l        Use long format (permissions, owner, size, date, etc.)
  -h        With -l, show file sizes in human-readable form (e.g. 1.0K,
            234M, 2.3G) instead of raw byte counts. No effect without -l.
  -1        Force single-column, one-entry-per-line output
  -C        Force multi-column output, even when standard output isn't
            a terminal
  -F        Append entry type indicators (/ @ * = |)
  -I        Show image thumbnails using iTerm2's inline image protocol.
            Ignored outside iTerm2, or when standard output isn't a
            terminal.
  --scale=n Multiply the -I thumbnail's width and height by n. Has an
            effect only in -1/-l (the only contexts -I itself is ever
            active in, since it's disabled outright on non-tty output).
            Omitting n is the same as 1. No effect without -I.
  -t        Sort by modification time, newest first
  -S        Sort by file size, largest first
  -X        Sort by extension
  -r        Reverse the sort order
  -d        List directories themselves, not their contents
  -R        Recursively list subdirectories encountered
  -B        Show directories in bold
  --color=when
            Control when to colorize output (always/auto/never).
            Omitting when is the same as always.
  --theme=mode
            Select the color gradient for the terminal's background
            (light/dark/auto). auto detects it from COLORFGBG, falling
            back to light if that isn't set. This is the default.
  --tag-colors=mode
            Select the Finder tag color palette (vivid/pastel), used
            only in 24-bit truecolor mode. Omitting mode is the same as
            pastel, the default.
  --columns=mode
            Select the multi-column layout mode (compact/classic).
            compact (the default) lets an unusually long name span
            multiple columns on its own row, so it doesn't force every
            column to widen -- but falls back to classic if that
            wouldn't actually fit more columns. classic always behaves
            like plain ls -C. Omitting mode is the same as compact.
  --tag=mode
            Select how Finder tags are shown (bg/dot/str/off). bg (the
            default) uses the color of the entry's last Finder tag, if
            any, as the entry's own background; extra tags beyond that
            one show as dots after the name. dot never sets a
            background from a tag; every tag (not just the extras)
            shows as a dot instead. str appends every tag's name after
            the entry as a bracketed comma-separated list (e.g.
            "report.pdf [Work, Urgent]"), each name colored with its
            own tag color where it has one, and never sets a
            background either. off shows no tag information at all.
            Omitting mode is the same as bg.
  --stripe  Tint every entry's background, filling the entry's full
            column width in multi-column output (alternating tint by
            column), or every odd row's whole line in -1/-l.
  --suffix-color=mode
            Select the color of the -F type indicator (/ @ * = |)
            (off/type). off (the default) colors it the same as
            the entry's name. type instead colors it by which
            character it is, matching /bin/ls -G's default per-type
            colors (/ blue, @ magenta, = green, | yellow, * red).
            Has no effect without -F.
  --fg-mode=mode
            Select whether a name's own foreground color is set from
            its recency gradient (date/off). date (the default) colors
            each name by how recently it was modified. off leaves
            names in the terminal's default foreground color; Finder
            tag and stripe backgrounds are unaffected either way.
            Omitting mode is the same as date.
  --base-fg=RRGGBB
            Override the color the oldest files fade to in the recency
            gradient (default: a guess based on --theme's light/dark
            setting), as 6 hex digits, e.g. 808080. The whole gradient
            is recomputed as a straight line from the cyan/magenta
            starting color to RRGGBB. No effect with --fg-mode=off.
  --quote   Quote a name whenever it contains whitespace, a shell
            metacharacter, or a control character, so it's safe to
            paste into a shell.
  --group-directories-first
            List directories before other entries, keeping whatever
            sort order (name/-t/-S/-X, each possibly reversed by -r)
            was already in effect within each group. A symlink to a
            directory counts as a directory here (matching GNU ls).
  --help    Show this help and exit
  --version Show the version number and exit

If an unsupported option is passed, it falls back to the standard ls command.""")


def plain_ls_fallback_argv_env(opt_color):
    """Returns (argv, env) to os.execvpe() into for the unsupported-option
    fallback, deciding whether it should be colorized the same way
    main() decides use_color for macls.py's own output (opt_color, the
    --color value parsed so far at the point the fallback triggers,
    defaulting to "auto" like macls.py's own default): "always" forces
    it on, "never" forces it off, and "auto" follows
    isatty()/CLICOLOR_FORCE. Forcing it on unconditionally (the previous
    behavior) leaked escape sequences into piped/redirected output
    whenever nothing asked for color -- exactly what plain ls itself
    would never do by default.

    -G (BSD ls, macOS) and --color=always (GNU ls, Linux) both request
    color; on Linux, ls's own -G instead means "don't print group
    names" -- a completely different, unrelated flag -- so which one to
    use can't be a single hardcoded value shared across platforms.

    On macOS, -G alone still isn't enough to force color into a
    pipe/file: BSD ls only colorizes non-tty output when CLICOLOR_FORCE
    is also set (see its man page) -- unlike GNU ls's --color=always,
    which forces on its own. So when colorize is True specifically
    because opt_color=="always" (i.e. isatty()/CLICOLOR_FORCE alone
    wouldn't have colorized), CLICOLOR_FORCE=1 is added to env for
    macOS's sake; passing it always would be harmless too, but only
    adding it when actually needed keeps the child's environment
    otherwise identical to this process's.
    """
    if opt_color == "always":
        colorize = True
    elif opt_color == "never":
        colorize = False
    else:
        colorize = sys.stdout.isatty() or bool(os.environ.get("CLICOLOR_FORCE"))
    if not colorize:
        return ["ls"], os.environ
    if sys.platform == "darwin":
        env = os.environ if os.environ.get("CLICOLOR_FORCE") else {**os.environ, "CLICOLOR_FORCE": "1"}
        return ["ls", "-G"], env
    return ["ls", "--color=always"], os.environ


# The mode-style long options (--color=when, --tag=mode, etc.),
# table-driven so parse_options() doesn't need one hand-written
# if-block per option: (long option name, the Options field it sets,
# the value used when the option is given bare with no "=value", the
# values die_invalid_value() accepts). Order matches OPTIONS in this
# file's own docstring/print_help().
MODE_OPTIONS = (
    ("--color", "color", "always", ("always", "auto", "never")),
    ("--theme", "theme", "auto", ("light", "dark", "auto")),
    ("--tag-colors", "tag_colors", "pastel", ("vivid", "pastel")),
    ("--columns", "columns", "compact", ("compact", "classic")),
    ("--tag", "tag", "bg", ("bg", "dot", "str", "off")),
    ("--suffix-color", "suffix_color", "off", ("off", "type")),
    ("--fg-mode", "fg_mode", "date", ("date", "off")),
)

# Long options macls.py recognizes that plain ls(1) doesn't know
# about, used by strip_macls_only_options() below to make the plain-ls
# fallback actually work instead of erroring out on them.
MACLS_ONLY_LONG_OPTS = tuple(name for name, *_ in MODE_OPTIONS) + ("--quote", "--group-directories-first", "--stripe", "--base-fg", "--scale", "--no-sips")


def strip_macls_only_options(argv):
    """Removes macls.py-only long options (MACLS_ONLY_LONG_OPTS,
    bare or "=value") from argv, for re-exec'ing into plain ls(1) when
    falling back for an option ls itself doesn't support (e.g. -R):
    ls would otherwise choke on --tag=bg etc. still being
    present in argv alongside the option that actually triggered the
    fallback. Mirrors parse_options()'s own GNU-style permutation: an
    option is stripped wherever it appears in argv, not just before the
    first positional argument, so "file --tag=bg" strips --tag=bg the
    same as "--tag=bg file" would. Only "--" stops this -- everything at
    or after it (including something that looks like one of these
    options) is left untouched, since it's a literal positional argument
    there.

    Returns the filtered copy of argv.
    """
    result = []
    stop = False
    for arg in argv:
        if stop:
            result.append(arg)
            continue
        if arg == "--":
            stop = True
            result.append(arg)
            continue
        if arg == "-" or not arg.startswith("-"):
            result.append(arg)
            continue
        if any(arg == opt or arg.startswith(opt + "=") for opt in MACLS_ONLY_LONG_OPTS):
            continue
        result.append(arg)
    return result


def pre_scan_opt_color(argv):
    """Scans argv for a --color/--color=value ahead of parse_options()'s
    own left-to-right pass, mirroring its GNU-style option/positional
    handling ("--" stops option scanning, but a positional argument
    before it doesn't) and its "last one wins" handling of a repeated
    flag. An unsupported option earlier in argv (e.g. "-x --color=always")
    triggers plain_ls_fallback_argv_env() before parse_options()'s own
    loop ever reaches --color, so without this, that fallback would fall
    back to "auto" and could stay uncolored even though --color=always
    appears later in the same command line. An invalid value here is left
    to parse_options()'s own pass to actually report/fall back on -- this
    only feeds the color decision available to an earlier fallback, so an
    invalid value is simply ignored (kept as the previous value) rather
    than acted on.

    Returns "always", "auto", or "never".
    """
    value = "auto"
    for arg in argv:
        if arg == "--":
            break
        if arg == "-" or not arg.startswith("-"):
            continue
        if arg == "--color" or arg.startswith("--color="):
            candidate = arg.split("=", 1)[1] if "=" in arg else "always"
            if candidate in ("always", "auto", "never"):
                value = candidate
    return value


def die_invalid_value(option, value, choices):
    """Prints a usage error for an invalid value given to a mode-style
    long option (--tag=xyz, --fg-mode=xyz, etc.) and exits(2).
    Distinct from the unsupported-option fallback (see
    plain_ls_fallback_argv_env()): an option macls.py doesn't
    recognize at all falls back to plain ls, but a recognized option
    given a value it doesn't understand is a usage mistake worth
    surfacing directly rather than silently changing behavior."""
    sys.stderr.write(
        f"{PROG}: invalid value '{value}' for {option} "
        f"(must be one of: {', '.join(choices)})\n"
    )
    sys.exit(2)


def parse_hex_rgb(value):
    """Parses a 6-hex-digit RRGGBB string (see --base-fg) into an
    (r, g, b) tuple, or None if value isn't exactly 6 hex digits."""
    if len(value) != 6:
        return None
    try:
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def die_invalid_base_fg(value):
    """Prints a usage error for an invalid --base-fg value and exits(2)
    -- distinct from die_invalid_value() since --base-fg's valid values
    (any 6-hex-digit RRGGBB string) aren't a fixed list of choices."""
    sys.stderr.write(
        f"{PROG}: invalid value '{value}' for --base-fg "
        f"(must be 6 hex digits, e.g. 808080)\n"
    )
    sys.exit(2)


def parse_positive_int(value):
    """Parses value as a positive (>=1) base-10 integer (see --scale),
    or None if it isn't one."""
    if not value.isdigit():
        return None
    n = int(value)
    return n if n >= 1 else None


def die_invalid_scale(value):
    """Prints a usage error for an invalid --scale value and exits(2)
    -- distinct from die_invalid_value() since --scale's valid values
    (any positive integer) aren't a fixed list of choices."""
    sys.stderr.write(
        f"{PROG}: invalid value '{value}' for --scale "
        f"(must be a positive integer, e.g. 2)\n"
    )
    sys.exit(2)


def parse_options(argv):
    """Parses short options (-a -A -l -h -1 -C -F -I -t -d -B -R -S -X -r, combinable). GNU-style:
    options may be freely mixed with positional arguments in any order
    (unlike POSIX getopts, parsing doesn't stop at the first non-option
    argument) -- "macls.py file.txt -l" works the same as
    "macls.py -l file.txt". A literal "--" stops option parsing outright;
    everything after it, even something that looks like an option, is
    taken as a positional argument. Falls back to plain ls (colorized) if
    an unsupported option is found; exits with an error (see
    die_invalid_value()) if a recognized mode-style option is given a
    value it doesn't understand.
    If --help or --version is passed, prints the corresponding message
    and exits.

    -1/-C/-l are mutually exclusive display formats (matching real ls's
    own -1/-C/-x/-l handling): whichever is given last on the command
    line wins, clearing whichever of the other two was set earlier.

    Returns (opts, positional): an Options instance and the list of
    positional (non-option) arguments, in the order they were given.
    """
    opts = Options(color=pre_scan_opt_color(argv))
    positional = []
    stop_options = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if stop_options:
            positional.append(arg)
            i += 1
            continue
        if arg == "--help":
            print_help()
            sys.exit(0)
        if arg == "--version":
            print(f"{PROG} {VERSION}")
            sys.exit(0)
        matched_mode_option = False
        for name, field, bare_value, choices in MODE_OPTIONS:
            if arg == name or arg.startswith(name + "="):
                value = arg.split("=", 1)[1] if "=" in arg else bare_value
                if value not in choices:
                    die_invalid_value(name, value, choices)
                setattr(opts, field, value)
                matched_mode_option = True
                break
        if matched_mode_option:
            i += 1
            continue
        if arg == "--quote":
            opts.quote = True
            i += 1
            continue
        if arg == "--group-directories-first":
            opts.group_dirs_first = True
            i += 1
            continue
        if arg == "--stripe":
            opts.stripe = True
            i += 1
            continue
        if arg == "--no-sips":
            # Undocumented escape hatch: skips _sips_shrink_image()
            # entirely, sending -I thumbnails at their original
            # resolution again (the pre-sips behavior). Exists for
            # comparing/debugging sips's own effect on thumbnail speed
            # and quality, not for end users -- see SIPS_RESIZE_THRESHOLD_BYTES.
            opts.no_sips = True
            i += 1
            continue
        if arg == "--base-fg" or arg.startswith("--base-fg="):
            value = arg.split("=", 1)[1] if "=" in arg else ""
            rgb = parse_hex_rgb(value)
            if rgb is None:
                die_invalid_base_fg(value)
            opts.base_fg = rgb
            i += 1
            continue
        if arg == "--scale" or arg.startswith("--scale="):
            value = arg.split("=", 1)[1] if "=" in arg else ""
            n = parse_positive_int(value)
            if n is None:
                die_invalid_scale(value)
            opts.scale = n
            i += 1
            continue
        if arg == "--":
            stop_options = True
            i += 1
            continue
        if arg == "-" or not arg.startswith("-"):
            positional.append(arg)
            i += 1
            continue
        for ch in arg[1:]:
            if ch == "a":
                opts.a = True
            elif ch == "A":
                opts.A = True
            elif ch == "l":
                opts.l = True
                opts.one = False
                opts.C = False
            elif ch == "h":
                opts.h = True
            elif ch == "1":
                opts.one = True
                opts.l = False
                opts.C = False
            elif ch == "C":
                opts.C = True
                opts.l = False
                opts.one = False
            elif ch == "F":
                opts.f = True
            elif ch == "I":
                opts.i = True
            elif ch == "t":
                opts.t = True
            elif ch == "d":
                opts.d = True
            elif ch == "B":
                opts.b = True
            elif ch == "R":
                opts.r = True
            elif ch == "S":
                opts.S = True
            elif ch == "X":
                opts.X = True
            elif ch == "r":
                opts.reverse = True
            else:
                # Fall back to plain ls (colorized) for unsupported options.
                argv_fb, env_fb = plain_ls_fallback_argv_env(opts.color)
                os.execvpe("ls", argv_fb + strip_macls_only_options(argv), env_fb)
        i += 1
    return opts, positional


def sort_dir_args(dir_args):
    """Sorts multiple directory arguments in locale order (matching
    sort(1)'s default behavior). Returns the sorted list."""
    try:
        locale.setlocale(locale.LC_COLLATE, "")
        return sorted(dir_args, key=locale.strxfrm)
    except (locale.Error, OSError):
        # macOS's libc has a bug where strxfrm() raises Errno 22
        # (Invalid argument) when converting certain multibyte strings
        # (e.g. Japanese).
        return sorted(dir_args)


def main():
    argv = sys.argv[1:]
    opts, positional = parse_options(argv)

    if opts.color == "always":
        opts.use_color = True
    elif opts.color == "never":
        opts.use_color = False
    else:
        opts.use_color = sys.stdout.isatty() or bool(os.environ.get("CLICOLOR_FORCE"))

    if opts.theme == "auto":
        detected = detect_dark_background()
        opts.theme = "dark" if detected else "light"

    opts.use_truecolor = opts.use_color and supports_truecolor()

    if opts.i and not sys.stdout.isatty():
        opts.i = False
    elif opts.i and not iterm2_supported():
        print(f"{PROG}: -I requires iTerm2; disabling thumbnails", file=sys.stderr)
        opts.i = False

    # From here, handle the (possibly multiple) arguments. As with real
    # ls, non-directory arguments are grouped together, sorted, and
    # listed first, followed by directory arguments in name order, each
    # with its contents listed. A "path:" header is only added before a
    # directory listing when there are 2 or more arguments total
    # (matching real ls's behavior). This applies even with -R: a lone
    # top-level directory argument still gets no header (it's the
    # implicit subject, no ambiguity to resolve), but every subdirectory
    # -R recurses into does, since from there on multiple directories
    # are in play (list_target() always passes show_header=True for
    # those recursive calls, regardless of this).
    args = positional if positional else ["."]

    exit_code = 0
    valid_args = []
    for a in args:
        # Treat broken symlinks as valid arguments too, matching ls.
        if not os.path.lexists(a):
            print(f"{PROG}: {a}: No such file or directory", file=sys.stderr)
            exit_code = 1
            continue
        valid_args.append(a)

    if not valid_args:
        sys.exit(exit_code)

    show_headers = len(args) > 1

    file_args = []
    dir_args = []
    for a in valid_args:
        if not opts.d and os.path.isdir(a):
            dir_args.append(a)
        else:
            file_args.append(a)

    if len(dir_args) > 1:
        dir_args = sort_dir_args(dir_args)

    section_printed = False

    if file_args:
        list_target("files", False, file_args, opts)
        section_printed = True

    for d in dir_args:
        if section_printed:
            print()
        list_target("dir", show_headers, [d], opts)
        section_printed = True

    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Exit quietly instead of printing a traceback; 128+SIGINT (2) is
        # the conventional exit code for a Ctrl-C interrupted process.
        sys.exit(130)
