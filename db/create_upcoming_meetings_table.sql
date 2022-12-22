CREATE TABLE public.upcoming
(
    id character varying NOT NULL,
    language character varying(2),
    path character varying,
    url character varying,
    name character varying,
    html character varying,
    date_raw character varying,
    date_parsed date,
    start_time_raw character varying,
    start_time_parsed time with time zone,
    location character varying,
    meeting_no character varying,
    live_stream_str character varying,
    live_stream_url character varying,
    timestamp_utc timestamp NOT NULL,
    PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.upcoming
    OWNER to postgres;

COMMENT ON TABLE public.upcoming
    IS 'Upcoming TTC meetings';
