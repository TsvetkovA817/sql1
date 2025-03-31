-- Postgres sql
-- Cоздание бд 

CREATE DATABASE muzdb
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;


CREATE SCHEMA dt
    AUTHORIZATION postgres;
	
--

CREATE TABLE dt.genres  -- Создание таблицы genres в схеме dt
(
    id serial NOT NULL,  -- Автоинкрементный целочисленный ID (не может быть NULL)
    name character varying(60) NOT NULL,  -- Строка длиной до 60 символов (не может быть NULL)
    PRIMARY KEY (id)  -- Установка id как первичного ключа
)
WITH (
    OIDS = FALSE  -- Отключение устаревшего механизма OIDs (объектных идентификаторов)
);

ALTER TABLE IF EXISTS dt.genres
    OWNER to postgres;
	
COMMENT ON TABLE dt.genres IS 'Справочник музыкальных жанров';
COMMENT ON COLUMN dt.genres.name IS 'Название жанра (макс. 60 символов)';

--

CREATE TABLE dt.artists  -- Создание таблицы artists в схеме dt
(
    id serial NOT NULL,  -- Автоинкрементный целочисленный ID (не может быть NULL)
    name character varying(60) NOT NULL,  -- Строка длиной до 60 символов (не может быть NULL)
    PRIMARY KEY (id)  -- Установка id как первичного ключа
)
WITH (
    OIDS = FALSE  -- Отключение устаревшего механизма OIDs (объектных идентификаторов)
);

ALTER TABLE IF EXISTS dt.artists
    OWNER to postgres;
	
COMMENT ON TABLE dt.artists IS 'Справочник исполнителей';
COMMENT ON COLUMN dt.artists.name IS 'Название исполнителя (макс. 60 символов)';

--

CREATE TABLE dt.albums
(
    id serial NOT NULL,
    name character varying(60) NOT NULL,
    year integer,
    PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE IF EXISTS dt.albums
    OWNER to postgres;

COMMENT ON TABLE dt.albums
    IS 'Альбомы';
	
--

CREATE TABLE dt.collections
(
    id serial NOT NULL,
    name character varying(60),
    year integer,
    PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
);

ALTER TABLE IF EXISTS dt.collections
    OWNER to postgres;

COMMENT ON TABLE dt.collections
    IS 'Музыкальные сборники';

--

-- 

DROP TABLE IF EXISTS dt.tracks;

CREATE TABLE IF NOT EXISTS dt.tracks
(
    id integer NOT NULL DEFAULT nextval('dt.tracks_id_seq'::regclass),
    name character varying(60) COLLATE pg_catalog."default" NOT NULL,
    album_id integer NOT NULL,
    CONSTRAINT tracks_pkey PRIMARY KEY (id),
    CONSTRAINT album FOREIGN KEY (album_id)
        REFERENCES dt.albums (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS dt.tracks
    OWNER to postgres;

COMMENT ON TABLE dt.tracks
    IS 'Музыкальные треки';
	
--

-- 
-- Удаляет таблицу genre_artist в схеме dt, если она существует
-- Позволяет избежать ошибок при повторном выполнении скрипта
DROP TABLE IF EXISTS dt.genre_artist;
-- Создает таблицу только если она еще не существует
CREATE TABLE IF NOT EXISTS dt.genre_artist
(   -- первичный ключ с автоинкрементом через последовательность
    id integer NOT NULL DEFAULT nextval('dt.genre_artist_id_seq'::regclass),
    genre_id integer,  -- внешний ключ к таблице жанров
    artist_id integer, -- - внешний ключ к таблице артистов
	--  первичный ключ с именем genre_artist_pkey на поле id
    CONSTRAINT genre_artist_pkey PRIMARY KEY (id), 
	-- Два внешних ключа, на таблицы artists и genres
    CONSTRAINT artist FOREIGN KEY (artist_id)
	    -- стандартное поведение при проверке внешнего ключа
        REFERENCES dt.artists (id) MATCH SIMPLE 
		-- запрет изменений, которые нарушат ссылочную целостность
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
		-- ограничение создается без проверки существующих данных
        NOT VALID,
    CONSTRAINT genre FOREIGN KEY (genre_id)
        REFERENCES dt.genres (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
WITH (
    OIDS = FALSE -- отключает устаревшие объектные идентификаторы
)
TABLESPACE pg_default; --  таблица создается в пространстве по умолчанию
-- Устанавливает владельца таблицы пользователь postgres
ALTER TABLE IF EXISTS dt.genre_artist
    OWNER to postgres;


--

-- Удаляет таблицу artist_album в схеме dt, если она существует
-- Позволяет избежать ошибок при повторном выполнении скрипта
DROP TABLE IF EXISTS dt.artist_album;

CREATE TABLE IF NOT EXISTS dt.artist_album
(
    id integer NOT NULL DEFAULT nextval('dt.artist_album_id_seq'::regclass),
    artist_id integer,
    album_id integer,
    CONSTRAINT artist_album_pkey PRIMARY KEY (id),
    CONSTRAINT album FOREIGN KEY (album_id)
        REFERENCES dt.albums (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT artist FOREIGN KEY (artist_id)
        REFERENCES dt.artists (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS dt.artist_album
    OWNER to postgres;


--


DROP TABLE IF EXISTS dt.collection_track;

CREATE TABLE IF NOT EXISTS dt.collection_track
(
    id integer NOT NULL DEFAULT nextval('dt.collection_track_id_seq'::regclass),
    track_id integer,
    collection_id integer,
    CONSTRAINT collection_track_pkey PRIMARY KEY (id),
    CONSTRAINT collection FOREIGN KEY (collection_id)
        REFERENCES dt.collections (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT track FOREIGN KEY (track_id)
        REFERENCES dt.tracks (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS dt.collection_track
    OWNER to postgres;
