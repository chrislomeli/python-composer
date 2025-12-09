-- 0001_create_notes_table.sql
-- Drop existing (careful in prod!) and create the notes table for MVP.
DROP TABLE IF EXISTS public.notes CASCADE;
DROP SEQUENCE IF EXISTS public.notes_id_seq;

CREATE SEQUENCE public.notes_id_seq AS integer START 1;

CREATE TABLE public.notes
(
    id                integer NOT NULL DEFAULT nextval('public.notes_id_seq'::regclass),
    absolute_pitch    smallint NOT NULL CHECK (absolute_pitch BETWEEN 0 AND 127),
    cents_offset      double precision DEFAULT 0.0,     -- fine tuning in cents
    start_beats       double precision NOT NULL,        -- fractional beats (or seconds if you use seconds)
    duration_beats    double precision NOT NULL,        -- duration in beats
    velocity          smallint NOT NULL DEFAULT 90 CHECK (velocity BETWEEN 0 AND 127),
    articulation      text DEFAULT 'normal',            -- staccato, legato, etc.
    instrument        text,                             -- optional instrument/patch name
    track_id          integer,                          -- reference to a track table if you have one

    -- Optional semantic fields (nullable)
    scale_degree      smallint,                         -- 1..7 relative to tonal center (nullable)
    interval_prev     smallint,                         -- signed semitone difference from previous note

    -- Expression and metadata as JSONB for flexible storage
    expression        jsonb,                            -- { "cc": { "1": [{time:,value:},...] }, "pitch_bend": [...] }
    metadata          jsonb,                            -- freeform metadata (tags, provenance)

    created_at        timestamp with time zone DEFAULT now(),
    updated_at        timestamp with time zone DEFAULT now(),

    CONSTRAINT notes_pkey PRIMARY KEY (id)
);

ALTER SEQUENCE public.notes_id_seq OWNED BY public.notes.id;

-- Useful indexes for typical queries
CREATE INDEX idx_notes_track_start ON public.notes (track_id, start_beats);
CREATE INDEX idx_notes_pitch ON public.notes (absolute_pitch);
CREATE INDEX idx_notes_metadata_gin ON public.notes USING gin (metadata);
CREATE INDEX idx_expression_gin ON public.notes USING gin (expression);

-- Example foreign key additions if you have related tables:
-- ALTER TABLE public.notes ADD CONSTRAINT notes_track_fkey FOREIGN KEY (track_id) REFERENCES public.tracks(id) ON DELETE SET NULL;
