import os
import random
import mido
from mido import MidiFile, MidiTrack, MetaMessage, Message

# Expanded list of words to simulate different mouth movements
mouth_movement_words = [
    # Vowel sounds
    "aa", "ee", "oo", "ai", "au", "ea", "oa", "ou", "ei", "ie", "ui", "ae", "eu", "oe", "uo", "ay", "oy",

    # Simple consonant-vowel combinations
    "la", "ma", "ba", "pa", "fa", "sa", "da", "ka", "na", "ga", "ha", "ja", "cha", "sha", "tha", "ra", "ta", "za", "wa", "ya",

    # Complex consonant-vowel combinations
    "blu", "plu", "dra", "klo", "kra", "tra", "sha", "sla", "twi", "glu", "cli", "pro", "fro", "pri", "cru", "qua", "bro", "gro",

    # Nasal sounds
    "mm", "nn", "ng", "mn", "gn", "an", "in", "un", "on",

    # Plosive sounds
    "pa", "ba", "da", "ta", "ka", "ga", "pla", "bra", "dra", "cla", "kra", "gra", "tra", "qua",

    # Fricative sounds
    "fa", "va", "za", "sa", "sha", "tha", "cha", "ja", "sha", "za", "tha", "swa",

    # Diphthongs
    "ou", "oi", "ae", "au", "eu", "oe", "ai", "ay", "oy", "aw", "ew", "ow", "iu",

    # Lip and mouth movements
    "moo", "boo", "wow", "yaw", "woo", "bah", "maw", "yaw", "loh", "lah", "wah",

    # Consonant clusters
    "bl", "br", "tr", "kr", "fr", "pl", "dr", "cl", "gl", "sl", "pr", "gr", "st", "sp",

    # Soft sounds
    "lo", "me", "ba", "fa", "ho", "wo", "ye", "ra", "le", "mo", "po", "so"
]

# Configuration Parameters
MIN_PHRASE_LENGTH = 1200    # Minimum phrase length in ticks
SHORT_NOTE_THRESHOLD = 119   # Notes with duration <=119 ticks are short
LONG_NOTE_THRESHOLD = 120    # Notes with duration >=120 ticks are long
GAP_THRESHOLD = 20         # Gap in ticks to reset '+' assignment
PHRASE_GAP_THRESHOLD = 0 # Gap in ticks to reset '+' assignment

# Step 1.5: Remove overlapping notes in 'PART VOCALS' track
def remove_overlapping_notes(midi, track_name, note_range):
    """
    Removes notes within note_range from the specified track that start at the same time as another note.
    """
    for track in midi.tracks:
        if track_name.upper() in track.name.upper():
            print(f"Processing '{track_name}' track for overlapping notes.")
            abs_time = 0
            start_time_notes = {}
            overlapping_start_times = set()
            note_on_times = {}  # Track the start times of note_on events
            active_notes = {}  # Track active notes with their time to ensure proper pairing

            # First pass: Collect all note_on events within the note_range
            for msg in track:
                abs_time += msg.time
                if msg.type == 'note_on' and msg.note in note_range and msg.velocity > 0:
                    if abs_time in start_time_notes:
                        # Overlapping start time; mark this time for removal
                        overlapping_start_times.add(abs_time)
                        start_time_notes[abs_time].append(msg.note)
                    else:
                        start_time_notes[abs_time] = [msg.note]
                    # Track note_on time to pair with note_off later
                    note_on_times[msg.note] = abs_time
                    active_notes[msg.note] = abs_time  # Track active note and time

            if not overlapping_start_times:
                print("No overlapping notes found in the specified range.")
                return

            print(f"Found {len(overlapping_start_times)} start times with overlapping notes to remove.")

            # Second pass: Remove the identified overlapping notes and corresponding note_off events
            abs_time = 0
            new_track = MidiTrack()
            notes_kept_at_time = set()
            removed_notes = set()  # Track notes removed so their corresponding note_off can also be removed

            for msg in track:
                current_time = msg.time
                abs_time += current_time
                remove_msg = False

                if msg.type == 'note_on' and msg.note in note_range and msg.velocity > 0:
                    if abs_time in overlapping_start_times:
                        if abs_time not in notes_kept_at_time:
                            notes_kept_at_time.add(abs_time)
                            print(f"Keeping first note_on: Note {msg.note} at time {abs_time}")
                        else:
                            remove_msg = True
                            removed_notes.add(msg.note)  # Mark this note for removal
                            print(f"Removing subsequent note_on: Note {msg.note} at time {abs_time}")
                            active_notes.pop(msg.note, None)  # Remove from active notes when removing
                elif msg.type == 'note_off' and msg.note in note_range:
                    # Only remove note_off if its corresponding note_on was removed
                    if msg.note in removed_notes:
                        remove_msg = True  # Remove this note_off if its corresponding note_on was removed
                        removed_notes.discard(msg.note)  # Remove the note from the removed list after processing
                        print(f"Removing note_off: Note {msg.note} at time {abs_time}")
                    else:
                        print(f"Keeping note_off: Note {msg.note} at time {abs_time}")
                    # Ensure the note is no longer active once a note_off is encountered
                    active_notes.pop(msg.note, None)

                if not remove_msg:
                    new_track.append(msg)
                else:
                    # Adjust the time of subsequent messages to preserve timing
                    if new_track:
                        new_track[-1].time += current_time
                    else:
                        new_track.append(MetaMessage('track_name', name=track.name, time=0))

            # Replace the original track with the new track
            midi.tracks.remove(track)
            midi.tracks.append(new_track)
            print(f"Removed overlapping notes from '{track_name}' track.")
            break
    else:
        print(f"Track '{track_name}' not found in the MIDI file.")

def process_midi_file(midi_path):
    print(f"Processing {midi_path}")
    mid = MidiFile(midi_path)

    # Create a new track for PART VOCALS
    new_track = MidiTrack()
    new_track.append(MetaMessage('track_name', name='PART VOCALS', time=0))

    messages_with_abs_time = []
    note_events = []
    text_events = {}
    beat_times = []

    # Step 1: Identify BEAT track and collect down beat times
    for track in mid.tracks:
        if 'BEAT' in track.name.upper():
            total_time = 0
            for msg in track:
                total_time += msg.time
                if msg.type == 'note_on' and msg.note == 12 and msg.velocity > 0:
                    beat_times.append(total_time)
            break  # Assuming only one BEAT track

    if not beat_times:
        print(f"No down beats (note 12) found in BEAT track for {midi_path}. Cannot determine phrases.")
        return

    # Sort beat_times to ensure they are in ascending order
    beat_times = sorted(beat_times)

    remove_overlapping_notes(mid, track_name='PART VOCALS', note_range=range(96, 101))

    # Step 2: Process PART VOCALS track
    for track in mid.tracks:
        if 'PART VOCALS' in track.name.upper():
            total_time = 0
            for msg in track:
                total_time += msg.time

                # Skip original 'track_name' messages
                if msg.type == 'track_name':
                    continue

                # Create a copy of the message with time set to 0
                msg_copy = msg.copy(time=0)

                if msg.type in ['note_on', 'note_off']:
                    is_note_on = msg.type == 'note_on' and msg.velocity > 0
                    is_note_off = msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)

                    # Filter notes between 96 and 100, or note 116
                    if 96 <= msg.note <= 100:
                        if 96 <= msg.note <= 100:
                            # Move the note down by 18 semitones
                            msg_copy.note -= 18

                        # Collect the modified message
                        messages_with_abs_time.append((total_time, msg_copy))

                        # Collect note events for syllable processing (both note_on and note_off)
                        if 78 <= msg_copy.note <= 82:
                            note_events.append({
                                'time': total_time,
                                'msg': msg_copy,
                                'is_note_on': is_note_on,
                                'is_note_off': is_note_off
                            })
                    #elif msg.note == 116:
                    #    # Keep note 116 as is
                    #    messages_with_abs_time.append((total_time, msg_copy))
                else:
                    # Include other messages as is
                    messages_with_abs_time.append((total_time, msg_copy))

    # Step 3: Identify syllables from long and short notes
    if note_events:
        intervals = []
        current_notes = {}

        for event in note_events:
            note = event['msg'].note
            if event['is_note_on']:
                if note not in current_notes:
                    current_notes[note] = []
                current_notes[note].append(event['time'])
            elif event['is_note_off']:
                if note in current_notes and current_notes[note]:
                    start_time = current_notes[note].pop(0)  # FIFO for pairing
                    duration = event['time'] - start_time
                    if duration >= LONG_NOTE_THRESHOLD:
                        intervals.append({'start': start_time, 'end': event['time'], 'duration': duration, 'type': 'long'})
                    elif duration <= SHORT_NOTE_THRESHOLD:
                        intervals.append({'start': start_time, 'end': event['time'], 'duration': duration, 'type': 'short'})
                    else:
                        intervals.append({'start': start_time, 'end': event['time'], 'duration': duration, 'type': 'medium'})
                else:
                    # Note_off without a matching note_on
                    print(f"Warning: Note_off for note {note} at time {event['time']} without matching note_on.")

        # After processing all events, check for any unmatched note_on events
        for note, times in current_notes.items():
            for start_time in times:
                print(f"Warning: Note_on for note {note} at time {start_time} has no matching note_off.")

        # Sort intervals by start time
        intervals_sorted = sorted(intervals, key=lambda x: x['start'])

        #print(f"Minimum note length set to: {LONG_NOTE_THRESHOLD} ticks")
        #print(f"Number of long notes (duration >= {LONG_NOTE_THRESHOLD} ticks): {sum(1 for interval in intervals if interval['type'] == 'long')}")
        #print(f"Number of short notes (duration <= {SHORT_NOTE_THRESHOLD} ticks): {sum(1 for interval in intervals if interval['type'] == 'short')}")
        #print(f"Number of medium notes (duration > {SHORT_NOTE_THRESHOLD} and < {LONG_NOTE_THRESHOLD} ticks): {sum(1 for interval in intervals if interval['type'] == 'medium')}")
    else:
        print("No note events found in PART VOCALS track.")

    # Step 4: Define phrases based on beat_times and assign notes to phrases
    phrases = []  # List of [start_time, end_time]
    note_index = 0
    total_notes = len(intervals_sorted)

    previous_phrase_end = None  # Track the end time of the last phrase

    for i in range(len(beat_times) - 1):
        phrase_start = beat_times[i]
        phrase_end = beat_times[i + 1]

        # Ensure this phrase starts after the previous one
        if previous_phrase_end is not None and phrase_start <= previous_phrase_end:
            # Adjust the start time of the current phrase to ensure no overlap
            phrase_start = previous_phrase_end
            print(f"Adjusting phrase start to {phrase_start} to avoid overlap with previous phrase ending at {previous_phrase_end}")

        # Collect notes that start within this phrase
        notes_in_phrase = []
        while note_index < total_notes and intervals_sorted[note_index]['start'] < phrase_end:
            if intervals_sorted[note_index]['start'] >= phrase_start:
                notes_in_phrase.append(intervals_sorted[note_index])
            note_index += 1

        if not notes_in_phrase:
            continue  # No notes in this phrase

        # Determine the actual start and end of the phrase based on notes
        actual_start = min(note['start'] for note in notes_in_phrase)
        actual_end = max(note['end'] for note in notes_in_phrase)

        # Ensure the phrase meets the minimum length
        phrase_length = actual_end - actual_start
        if phrase_length < MIN_PHRASE_LENGTH:
            # Attempt to include notes from the next phrase
            if i + 1 < len(beat_times) - 1:
                next_phrase_start = beat_times[i + 1]
                next_phrase_end = beat_times[i + 2] if i + 2 < len(beat_times) else beat_times[-1] + (beat_times[-1] - beat_times[-2] if len(beat_times) >= 2 else MIN_PHRASE_LENGTH)

                # Collect notes from the next phrase that might be within the gap threshold
                temp_notes = []
                temp_index = note_index
                while temp_index < total_notes and intervals_sorted[temp_index]['start'] < next_phrase_end:
                    if (intervals_sorted[temp_index]['start'] - actual_end) <= PHRASE_GAP_THRESHOLD:
                        temp_notes.append(intervals_sorted[temp_index])
                        actual_end = max(actual_end, intervals_sorted[temp_index]['end'])
                        phrase_length = actual_end - actual_start
                    else:
                        break
                    temp_index += 1

                # If after adding the next phrase's notes, it meets the minimum length, create a combined phrase
                if phrase_length >= MIN_PHRASE_LENGTH:
                    phrases.append([actual_start, actual_end])
                    note_index = temp_index  # Skip ahead
                else:
                    # Still not enough, assign as is
                    phrases.append([actual_start, actual_end])
            else:
                # Last phrase, assign as is
                phrases.append([actual_start, actual_end])
        else:
            phrases.append([actual_start, actual_end])

        # Update previous_phrase_end to ensure the next phrase starts after this one
        previous_phrase_end = actual_end

    # Handle any remaining notes not assigned to any phrase
    while note_index < total_notes:
        note = intervals_sorted[note_index]
        if not phrases:
            phrases.append([note['start'], note['end']])
        else:
            last_phrase = phrases[-1]
            gap = note['start'] - last_phrase[1]
            if gap <= PHRASE_GAP_THRESHOLD:
                # Extend the last phrase to include this note
                print(f"Extending last phrase from {last_phrase[0]}-{last_phrase[1]} to include {note['start']}-{note['end']}")
                last_phrase[1] = max(last_phrase[1], note['end'])
            else:
                # Start a new phrase
                phrases.append([note['start'], note['end']])
        note_index += 1

    # Sort and remove duplicate phrases
    phrases = sorted(set(tuple(p) for p in phrases))
    phrases = [list(p) for p in phrases]

    # Step 5: Assign text events based on notes within phrases
    for phrase in phrases:
        phrase_start, phrase_end = phrase

        # Find notes within this phrase
        notes_in_phrase = [
            interval for interval in intervals_sorted
            if interval['start'] >= phrase_start and interval['end'] <= phrase_end
        ]

        if not notes_in_phrase:
            continue  # No notes in this phrase

        # Sort notes by start time
        notes_in_phrase_sorted = sorted(notes_in_phrase, key=lambda x: x['start'])

        # Initialize tracking to alternate between word and '+'
        assign_word_next = True  # This will toggle between word and '+'
        last_note_end_time = None  # Track the last note's end time

        for note in notes_in_phrase_sorted:
            syllable_start = note['start']
            syllable_type = note['type']

            # Check for a significant gap before assigning (always assign word after long gap)
            if last_note_end_time is not None and (syllable_start - last_note_end_time) > GAP_THRESHOLD:
                assign_word_next = True  # Reset to ensure word assignment after a gap

            if syllable_type == 'long':
                if assign_word_next:
                    # Assign a word to this long note
                    random_word = random.choice(mouth_movement_words)
                    if syllable_start not in text_events:
                        text_events[syllable_start] = random_word
                else:
                    # Assign '+' to the next long note
                    if syllable_start not in text_events:
                        text_events[syllable_start] = '+'

                # Toggle the assignment for the next long note
                assign_word_next = not assign_word_next
            else:
                # For short and medium notes, always assign a word
                random_word = random.choice(mouth_movement_words)
                if syllable_start not in text_events:
                    text_events[syllable_start] = random_word

            # Update the last_note_end_time for gap tracking
            last_note_end_time = note['end']

    # Step 6: Ensure no phrase starts with '+'
    phrases_sorted = sorted(phrases, key=lambda x: x[0])
    text_events_sorted = sorted(text_events.items(), key=lambda x: x[0])

    for phrase in phrases_sorted:
        phrase_start, _ = phrase
        # Find the first text event in the phrase
        first_text_event = next((te for te in text_events_sorted if te[0] >= phrase_start), None)
        if first_text_event and first_text_event[1] == '+':
            # Replace '+' with a random word
            new_word = random.choice(mouth_movement_words)
            text_events[first_text_event[0]] = new_word
            #print(f"Replaced '+' with '{new_word}' at time {first_text_event[0]} in phrase starting at {phrase_start}")

    # Step 7: Assign default lyrics to any missing vocal notes
    for phrase in phrases_sorted:
        phrase_start, phrase_end = phrase
        # Find notes within this phrase
        notes_in_phrase = [
            interval for interval in intervals_sorted
            if interval['start'] >= phrase_start and interval['end'] <= phrase_end
        ]
        for note in notes_in_phrase:
            syllable_start = note['start']
            syllable_type = note['type']
            if syllable_start not in text_events:
                if syllable_type == 'short':
                    # Assign a random word
                    default_word = random.choice(mouth_movement_words)
                    text_events[syllable_start] = default_word
                    print(f"Assigned default word '{default_word}' to short syllable at time {syllable_start}")
                elif syllable_type == 'long':
                    # Assign '+' to long syllables if not already assigned
                    text_events[syllable_start] = '+'
                    print(f"Assigned '+' to long syllable at time {syllable_start}")
                else:
                    # Assign a random word for medium syllables
                    default_word = random.choice(mouth_movement_words)
                    text_events[syllable_start] = default_word
                    print(f"Assigned default word '{default_word}' to medium syllable at time {syllable_start}")

    # Step 8: Merge all text events into messages_with_abs_time
    for abs_time, text in text_events.items():
        text_event = MetaMessage('text', text=text, time=0)
        messages_with_abs_time.append((abs_time, text_event))

    # Step 9: Create phrase indicator messages (note_on and note_off for note 105)
    for ps, pe in phrases_sorted:
        ps = int(ps)
        pe = int(pe)
        note_on_msg = Message('note_on', note=105, velocity=127, time=0)
        note_off_msg = Message('note_off', note=105, velocity=0, time=0)
        messages_with_abs_time.append((ps, note_on_msg))
        messages_with_abs_time.append((pe, note_off_msg))

    # Step 10: Sort all messages by absolute time and event type
    def event_sort_order(msg):
        if msg.type == 'note_off':
            return 0
        elif msg.type == 'note_on':
            return 1
        elif msg.type == 'text':
            return 2
        else:
            return 3  # Other messages

    messages_with_abs_time.sort(key=lambda x: (x[0], event_sort_order(x[1])))

    # Step 11: Convert absolute times back to delta times
    previous_time = 0
    for abs_time, msg in messages_with_abs_time:
        abs_time = int(abs_time)
        delta_time = abs_time - previous_time
        if delta_time < 0:
            print(f"Warning: Negative delta_time encountered at time {abs_time}. Setting delta_time to 0.")
            delta_time = 0
        msg.time = delta_time
        new_track.append(msg)
        previous_time = abs_time

    # Step 12: Replace the existing PART VOCALS track with the new one
    mid.tracks = [track for track in mid.tracks if 'PART VOCALS' not in track.name.upper()]
    mid.tracks.append(new_track)

    # Step 13: Save the modified MIDI file
    mid.save(midi_path)
    print(f"Finished processing {midi_path}")

def main(midi_path):
    if not os.path.isfile(midi_path):
        print(f"Error: The file '{midi_path}' does not exist.")
        sys.exit(1)

    try:
        process_midi_file(midi_path)
    except Exception as e:
        print(f"Error processing {midi_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <midi_file_path>")
        sys.exit(1)

    midi_path = sys.argv[1]
    main(midi_path)
