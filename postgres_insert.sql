-- Вставка, обновление данных

INSERT INTO dt.artists(name, id) VALUES ('Артист1', 1);
INSERT INTO dt.artists(name, id) VALUES ('Исполнитель2', 2);
INSERT INTO dt.artists(name, id) VALUES ('Исполнитель3', 3);
INSERT INTO dt.artists(name, id) VALUES ('Артист4', 4);
INSERT INTO dt.artists(name, id) VALUES ('Артист5', 5);

INSERT INTO dt.genres(id, name)	VALUES (1, 'жанр1');
INSERT INTO dt.genres(id, name)	VALUES (2, 'жанр2');
INSERT INTO dt.genres(id, name)	VALUES (3, 'жанр3');
INSERT INTO dt.genres(id, name)	VALUES (4, 'жанр4');

INSERT INTO dt.albums(id, name, year) VALUES (1, 'Альбом1', 2021);
INSERT INTO dt.albums(id, name, year) VALUES (2, 'Альбом2', 2022);
INSERT INTO dt.albums(id, name, year) VALUES (3, 'Альбом3', 2023);
INSERT INTO dt.albums(id, name, year) VALUES (4, 'Альбом4', 2024);

INSERT INTO dt.tracks(id, name, album_id) VALUES (1, 'трек1', 1);
INSERT INTO dt.tracks(id, name, album_id) VALUES (2, 'трек2', 1);
INSERT INTO dt.tracks(id, name, album_id) VALUES (3, 'трек3', 2);
INSERT INTO dt.tracks(id, name, album_id) VALUES (4, 'трек4', 2);
INSERT INTO dt.tracks(id, name, album_id) VALUES (5, 'трек5', 2);
INSERT INTO dt.tracks(id, name, album_id) VALUES (6, 'трек6', 3);
INSERT INTO dt.tracks(id, name, album_id) VALUES (7, 'трек7', 3);
INSERT INTO dt.tracks(id, name, album_id) VALUES (8, 'трек8', 4);
INSERT INTO dt.tracks(id, name, album_id) VALUES (9, 'трек9', 4),(10, 'трек10', 4);

INSERT INTO dt.collections(id, name, year) 
			   VALUES (1, 'Сборник1', 2021),
			   		  (2, 'Сборник2', 2022),
					  (3, 'Сборник3', 2023),
					  (4, 'Сборник4', 2024);
					  
INSERT INTO dt.artist_album(
	id, artist_id, album_id)
	VALUES (1, 1, 1), (2, 2, 2), (3, 3, 3), (4, 4, 4), (5, 5, 4);					  
					  
INSERT INTO dt.collection_track(
	id, track_id, collection_id)
	VALUES (1, 1, 1), (2, 2, 1), (3, 3, 1),
	       (4, 4, 2), (5, 5, 2), (6, 6, 2),
		   (7, 7, 3), (8, 8, 3), (9, 9, 3),
		  (10, 1, 4), (11, 5, 4), (12, 9, 4);

INSERT INTO dt.genre_artist(
	id, genre_id, artist_id)
	VALUES (1, 1, 1), (2, 2, 2), (3, 3, 3),
		   (4, 4, 4), (5, 2, 5), (6, 1, 2);			  
					  
ALTER TABLE IF EXISTS dt.tracks
    ADD COLUMN IF NOT EXISTS duration numeric(7, 2);
	
UPDATE dt.tracks SET duration=1 WHERE id=1;
UPDATE dt.tracks SET duration=2 WHERE id=2;
UPDATE dt.tracks SET duration=3 WHERE id=3;
UPDATE dt.tracks SET duration=2 WHERE id=4;
UPDATE dt.tracks SET duration=5 WHERE id=5;
UPDATE dt.tracks SET duration=6 WHERE id=6;
UPDATE dt.tracks SET duration=5.3 WHERE id=7;
UPDATE dt.tracks SET duration=3.21 WHERE id=8;
UPDATE dt.tracks SET duration=7 WHERE id=9;
UPDATE dt.tracks SET duration=5.4 WHERE id=10;
