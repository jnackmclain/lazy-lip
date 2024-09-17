# Lazy-Lip

## An easy way to generate lipsync for Encore style pad vocal charts for use in Rock Band Games.

Imagine the scenario, you just charted a nice custom song for use in Encore, a Fortnite Festival inspired rhythmn game.

Now you want to use the song in Rock Band, but it would be nice if the vocalist at least had lipsync.

You don't feel like making an actual Rock Band Vocals track, all your effort was just there for pad vocals.

Enter, Lazy-Lip.

This script will convert your pad vocals chart in the PART VOCALS track to a super basic Rock Band style pitched PART VOCALS.

This will allow compiling in Magma to generate a basic lipsync that follows the pad charted notes.

## Features:
1. **Syllable Assignment**: Assigns syllables (or sounds) based on the duration of notes in the `PART VOCALS` track. These syllables simulate a varied range mouth movements in game.
3. **Auto Phrase Addition**: Automatically generates vocal phrases to satisfy Magma
5. **Adds Slides for added "realism"**: In some cases will add slides if params are met in the note charting. This isnt a perfect system but adds lipsync variety and can help sell as well.

## How it Works:
1. **Shift Notes**:
   - The Expert Vocals chart from the pad PART VOCALS chart is moved to the valid pitch window, all other notes are removed to start with a clean vocal track. Events are carried over.
   
2. **Syllable Assignment**:
   - A random word is assigned to each note, simulating different mouth movements.
   - There is a special case where if a sustain is followed by another sustain within a short period, that note is turned into a slide.
   - This is used to loosely adhere to the idea that vocal flourishes on long notes are charted as a second note and don't neccesarily need the mouth to close and reopen.
   
3. **Assigning Phrases**:
   - The vocal track is divided into phrases based on beat times from the BEAT track. If a phrase is too short, it is extended with notes from subsequent phrases.
   
4. **Generating Output**:
   - The final MIDI file includes new lyric and phrase markers, which are embedded directly in the `PART VOCALS` track.

## Usage:

Run the script with the following command:

```bash
python script.py <midi_file_path>
```

Replace `<midi_file_path>` with the path to the MIDI file you want to process.

## Notes:
- If no `BEAT` track is found in the MIDI file, the script exits early.
- The script automatically detects syllables based on the note durations and assigns corresponding words or symbols.
- The script tries to produce a Magma valid midi, but I have seen a few minor failures that were easier to manually fix than try to debug this whole thing.

## Troubleshooting:
- **Error: No down beats found in BEAT track**: Ensure that the MIDI file has a `BEAT` track with note 12 as the downbeat.

## Example Mouth Movement Words:
- Vowel sounds: "aa", "ee", "oo"
- Simple consonants: "la", "ma", "ba"
- Complex consonants: "blu", "plu"
- Nasal sounds: "mm", "nn"
