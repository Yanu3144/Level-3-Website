CREATE TABLE `users` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_name` text UNIQUE NOT NULL,
  `email` text UNIQUE NOT NULL,
  `password` text NOT NULL,
  `role` text NOT NULL
);

CREATE TABLE `genre` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` text UNIQUE NOT NULL
);

CREATE TABLE `games` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `title` text NOT NULL,
  `genre_id` int NOT NULL,
  `developer` text NOT NULL,
  `release_date` datetime NOT NULL,
  `price` int NOT NULL,
  `description` text,
  `cover_image_url` text
);

CREATE TABLE `reviews` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `game_id` int NOT NULL,
  `rating` int NOT NULL COMMENT '1-10 scale',
  `review_text` text NOT NULL,
  `created_at` datetime NOT NULL
);

CREATE TABLE `ratings_breakdown` (
  `game_id` int PRIMARY KEY,
  `avg_score` float DEFAULT 0,
  `total_reviews` int DEFAULT 0,
  `five_star_count` int DEFAULT 0,
  `four_star_count` int DEFAULT 0,
  `three_star_count` int DEFAULT 0,
  `two_star_count` int DEFAULT 0,
  `one_star_count` int DEFAULT 0
);

CREATE TABLE `platforms` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `name` text UNIQUE NOT NULL
);

CREATE TABLE `game_platforms` (
  `game_id` int,
  `platform_id` int,
  PRIMARY KEY (`game_id`, `platform_id`)
);

CREATE TABLE `wishlist` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `game_id` int NOT NULL,
  `added_at` datetime DEFAULT (now())
);
