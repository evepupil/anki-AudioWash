# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Anki addon** (plugin) called "Audio Wash Player" that extracts and loops audio from cards studied today. The addon integrates into Anki 2.1.45+ and provides a standalone player window for background audio playback.

**Key Characteristics:**
- Simple Python addon with no build process or external dependencies beyond Anki
- Uses PyQt6 for UI (provided by Anki)
- Direct integration with Anki's collection database and media system
- Chinese codebase with extensive Chinese comments

## Architecture

The addon follows a **modular, layered architecture** with clear separation of concerns:

```
User clicks "Tools > Start Audio Wash"
    ↓
audio_wash_player.start_audio_wash() (orchestrator)
    ↓
    ├── CardQuery.get_today_cards() → queries Anki database for today's cards
    ├── AudioExtractor.extract_audio_files() → parses [sound:...] tags from card fields
    └── AudioPlayerWindow() → displays PyQt6 player UI and handles playback
```

### Module Responsibilities

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `__init__.py` | Addon entry point | Calls `init_addon()` |
| `audio_wash_player.py` | Main orchestrator | `start_audio_wash()`, `add_menu_item()` |
| `card_query.py` | Database queries | `CardQuery` class |
| `audio_extractor.py` | Audio file extraction | `AudioExtractor` class |
| `player_window.py` | Player UI | `AudioPlayerWindow` class (PyQt6 QDialog) |

### Data Flow

1. **Card Query**: Uses Anki search syntax (`added:1`, `rated:1`) to find today's new/reviewed cards
2. **Audio Extraction**: Regex pattern `\[sound:(.*?)\]` extracts audio filenames from card HTML
3. **Path Resolution**: Resolves full paths using `col.media.dir()`
4. **Playback**: QMediaPlayer with QAudioOutput handles audio playback with shuffle and loop

## Development Commands

**Installation/Testing:**
```bash
# The addon is already in the correct location
# To test changes, restart Anki after modifying code
# Access via: Tools → Start Audio Wash
```

**No build process** - This is a simple Python addon with no compilation, bundling, or external dependencies.

## Important Implementation Details

### Anki Day Reset Logic
Anki's "day" resets at 4 AM (not midnight). The `CardQuery` class accounts for this when querying "today's" cards.

### Maximum Cards Limit
Default limit is 200 cards. Modify in `audio_wash_player.py:34`:
```python
CardQuery(mw.col, max_cards=200)  # Change this value
```

### Audio Tag Format
Cards must contain `[sound:filename.mp3]` tags in their fields. The extractor validates file existence before adding to playlist.

### Player Window Behavior
- Independent window (parent=None) to avoid blocking Anki main interface
- Uses `Qt.WindowType.WindowStaysOnTopHint` for always-on-top behavior
- Maintains separate `original_playlist` and `shuffled_playlist` lists
- Auto-advances on `QMediaPlayer.MediaStatus.EndOfMedia` signal
- Supports configurable auto-loop and interval settings
- Closing window stops playback and destroys instance

### Global State
The player window is stored as a global variable `_player_window` in `audio_wash_player.py` to prevent garbage collection and allow only one instance at a time.

## Code Style

- **Language**: Python 3.9+ with type hints (`List`, `int`, `str`, `dict`)
- **Comments**: Extensive Chinese comments throughout (preserve this style)
- **Naming**: Snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Uses Anki's `showInfo()` and `showWarning()` for user feedback
- **No logging system**: Relies on Anki's built-in message dialogs

## Anki API Usage

**Key Anki APIs used:**
- `mw.col` - Main collection object
- `mw.col.find_cards(query)` - Search cards using Anki query syntax
- `mw.col.get_card(card_id)` - Retrieve card object
- `mw.col.get_note(note_id)` - Retrieve note object
- `mw.col.media.dir()` - Get media directory path
- `aqt.utils.showInfo()` / `showWarning()` - Display messages
- `aqt.gui_hooks.main_window_did_init.append()` - Hook into Anki startup

## Testing the Addon

1. Make code changes
2. Restart Anki (Ctrl+Q or File > Exit)
3. Click Tools > Start Audio Wash
4. Verify behavior with test cards containing `[sound:...]` tags

**Creating test cards:**
- Ensure you have cards with audio fields like `[sound:audio.mp3]`
- Study/review some cards today to populate the query results
- The addon will show a warning if no audio files are found

## Common Modifications

**Changing query logic**: Edit `card_query.py` - modify `_get_new_cards_today()` or `_get_reviewed_cards_today()`

**Changing audio extraction**: Edit `audio_extractor.py` - modify regex pattern or `_extract_from_card()`

**Changing UI**: Edit `player_window.py` - modify `_init_ui()` or add new controls

**Adding menu items**: Edit `audio_wash_player.py` - modify `add_menu_item()`

**Adjusting loop settings**: Default auto-loop is enabled with 0-second interval. Users can configure via UI:
- Auto-loop checkbox (default: checked)
- Interval spinbox (default: 0 seconds, max: 60 seconds)
