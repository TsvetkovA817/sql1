-- Выборки

-- 2.1 Самый продолжительный трек

SELECT id, name, album_id, duration
	FROM dt.tracks
	ORDER BY duration DESC
	LIMIT 1;

-- 2.2 Название треков, продолжительность которых не менее 3,5 минут	
	
SELECT name, duration
	FROM dt.tracks
	where duration < 3.5
	ORDER BY duration;

-- 2.3 Названия сборников, вышедших в период с 2022 по 2024 год включительно	

SELECT id, name, year
	FROM dt.collections
	WHERE year BETWEEN 2022 AND 2024;

-- 2.4 Исполнители, чьё имя состоит из одного слова

UPDATE dt.artists SET name = 'Исполнитель 3' WHERE id=3;
UPDATE dt.artists SET name = 'Артист 4' WHERE id=4;

SELECT id, name
FROM dt.artists
WHERE trim(name) NOT LIKE '% %'
  AND trim(name) != '';

-- 2.5 Название треков, которые содержат слово 'мой' или 'my'	

UPDATE dt.tracks SET name='my track3' WHERE id=3;
UPDATE dt.tracks SET name='track my4' WHERE id=4;
UPDATE dt.tracks SET name='мой track6' WHERE id=6;
UPDATE dt.tracks SET name='track мой 7' WHERE id=7;

SELECT id, name, album_id, duration
	FROM dt.tracks
	WHERE name LIKE '%my%' OR name LIKE '%мой%';	


-- 3.1 Количество исполнителей в каждом жанре

SELECT 
    g.id AS genre_id,
    g.name AS genre_name,
    COUNT(DISTINCT ga.artist_id) AS artists_count
FROM 
    dt.genres g
LEFT JOIN 
    dt.genre_artist ga ON g.id = ga.genre_id
GROUP BY 
    g.id, g.name
ORDER BY 
    artists_count DESC;

-- 3.2 Количество треков, вошедших в альбомы 2021–2024 годов	

SELECT 
    COUNT(t.id) AS tracks_count
FROM 
    dt.tracks t
JOIN 
    dt.albums a ON t.album_id = a.id
WHERE 
    a.year BETWEEN 2021 AND 2024;

-- 3.3 Средняя продолжительность треков по каждому альбому

SELECT 
    al.id,
    al.name ,
    COUNT(tr.id) AS tracks_count,
	avg(tr.duration)
FROM 
    dt.albums al
JOIN 
    dt.tracks tr ON tr.album_id = al.id
group by al.id, al.name
order by al.name


-- 3.4.1 Все исполнители, которые не выпустили альбомы в 2024 году

SELECT 
    ar.id,
    ar.name,
	al.year
FROM 
    dt.artists ar
JOIN 
    dt.artist_album aa ON aa.artist_id = ar.id
JOIN
	dt.albums al ON aa.album_id = al.id
where al.year != 2024	
order by ar.name

-- 3.4.2 Все исполнители, которые не выпустили альбомы в 2024 году

SELECT ar.id, ar.name
FROM dt.artists ar
WHERE ar.id NOT IN (
    SELECT DISTINCT aa.artist_id
    FROM dt.artist_album aa
    JOIN dt.albums al ON aa.album_id = al.id
    WHERE al.year = 2024
)
ORDER BY ar.name;


-- 3.5.1 Названия сборников, в которых присутствует конкретный исполнитель

SELECT DISTINCT c.id, c.name AS collection_title
FROM dt.collections c
JOIN dt.collection_track ct ON c.id = ct.collection_id
JOIN dt.tracks t ON ct.track_id = t.id
JOIN dt.artist_album aa ON t.album_id = aa.album_id
JOIN dt.artists a ON aa.artist_id = a.id
WHERE a.name LIKE '%Артист1%'
ORDER BY c.name;


-- 3.5.2 Названия сборников, в которых присутствует конкретный исполнитель

SELECT 
    co.id AS collection_id,
    co.name AS collection_title,
    COUNT(DISTINCT tr.id) AS tracks_count,
    STRING_AGG(DISTINCT tr.name, ', ' ORDER BY tr.name) AS track_titles
FROM 
    dt.collections co
JOIN 
    dt.collection_track ct ON co.id = ct.collection_id
JOIN 
    dt.tracks tr ON ct.track_id = tr.id
JOIN 
    dt.artist_album aa ON tr.album_id = aa.album_id
WHERE 
    aa.artist_id = 2  -- id конкретного артиста
GROUP BY 
    co.id, co.name
ORDER BY 
    co.name;



-- 4.1 Названия альбомов, в которых присутствуют исполнители более чем одного жанра

SELECT DISTINCT a.id, a.name AS album_title
FROM dt.albums a
JOIN dt.artist_album aa ON a.id = aa.album_id
WHERE aa.artist_id IN (
    SELECT artist_id AS genre_count
    FROM dt.genre_artist
    GROUP BY artist_id
    HAVING COUNT(DISTINCT genre_id) > 1
)
ORDER BY a.name;

