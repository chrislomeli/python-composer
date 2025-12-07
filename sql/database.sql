-- ======================================
-- 1. Clips
-- The musical idea (bassline, melody, etc.)
-- ======================================

CREATE TABLE clips (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    style           TEXT,
    instrument      TEXT,
    tempo_bpm       INT,          -- optional (clips can be tempo-agnostic)
    grid_units      INT NOT NULL DEFAULT 32,   -- sub-beat grid per bar
    metadata        JSONB,        -- optional tags, notes, etc.
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast tag/style querying
CREATE INDEX clips_style_idx ON clips(style);
CREATE INDEX clips_metadata_gin_idx ON clips USING GIN (metadata);


-- ======================================
-- 2. Bars
-- Bars belonging to a clip
-- ======================================

CREATE TABLE bars (
    id              SERIAL PRIMARY KEY,
    clip_id         INT NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    bar_number      INT NOT NULL,
    time_signature_numerator   INT NOT NULL DEFAULT 4,
    time_signature_denominator INT NOT NULL DEFAULT 4,
    metadata        JSONB
);

-- A clip cannot have duplicate bar numbers
CREATE UNIQUE INDEX bars_clip_bar_unique_idx
    ON bars(clip_id, bar_number);


-- ======================================
-- 3. Notes
-- Atomic notes stored inside bars
-- ======================================

CREATE TABLE notes (
    id              SERIAL PRIMARY KEY,
    bar_id          INT NOT NULL REFERENCES bars(id) ON DELETE CASCADE,

    -- Timing: all in "grid units", where 32 units = 1 bar by default
    start_unit      INT NOT NULL,
    duration_units  INT NOT NULL,

    -- Pitch
    pitch_name      TEXT NOT NULL,     -- "C", "Db", "A"
    octave          INT NOT NULL,      -- 0–8
    midi_pitch      INT GENERATED ALWAYS AS (
                        CASE
                            WHEN pitch_name IS NOT NULL AND octave IS NOT NULL
                            THEN
                                (
                                    -- Formula: MIDI = base(C=0)+semitone_offset + (octave+1)*12
                                    (CASE pitch_name
                                        WHEN 'C'  THEN 0
                                        WHEN 'C#' THEN 1
                                        WHEN 'Db' THEN 1
                                        WHEN 'D'  THEN 2
                                        WHEN 'D#' THEN 3
                                        WHEN 'Eb' THEN 3
                                        WHEN 'E'  THEN 4
                                        WHEN 'F'  THEN 5
                                        WHEN 'F#' THEN 6
                                        WHEN 'Gb' THEN 6
                                        WHEN 'G'  THEN 7
                                        WHEN 'G#' THEN 8
                                        WHEN 'Ab' THEN 8
                                        WHEN 'A'  THEN 9
                                        WHEN 'A#' THEN 10
                                        WHEN 'Bb' THEN 10
                                        WHEN 'B'  THEN 11
                                    END)
                                    + (octave + 1) * 12
                                )
                            ELSE NULL
                        END
                    ) STORED,

    velocity        INT NOT NULL DEFAULT 90,     -- 1–127
    articulation    TEXT DEFAULT 'normal',        -- staccato/accent/etc.

    is_rest         BOOLEAN DEFAULT FALSE,        -- REST support
    metadata        JSONB
);

-- Improve timing queries
CREATE INDEX notes_bar_start_idx ON notes(bar_id, start_unit);
CREATE INDEX notes_bar_pitch_idx ON notes(bar_id, midi_pitch);
CREATE INDEX notes_metadata_gin_idx ON notes USING GIN (metadata);
