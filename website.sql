CREATE TABLE [users] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [user_name] text UNIQUE NOT NULL,
  [email] text UNIQUE NOT NULL,
  [password] text NOT NULL,
  [role] text NOT NULL
)
GO

CREATE TABLE [genre] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] text UNIQUE NOT NULL
)
GO

CREATE TABLE [games] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [title] text NOT NULL,
  [genre_id] int NOT NULL,
  [developer] text NOT NULL,
  [release_date] datetime NOT NULL,
  [price] int NOT NULL,
  [description] text,
  [cover_image_url] text
)
GO

CREATE TABLE [reviews] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [user_id] int NOT NULL,
  [game_id] int NOT NULL,
  [rating] int NOT NULL,
  [review_text] text NOT NULL,
  [created_at] datetime NOT NULL
)
GO

CREATE TABLE [ratings_breakdown] (
  [game_id] int PRIMARY KEY,
  [avg_score] float DEFAULT (0),
  [total_reviews] int DEFAULT (0),
  [five_star_count] int DEFAULT (0),
  [four_star_count] int DEFAULT (0),
  [three_star_count] int DEFAULT (0),
  [two_star_count] int DEFAULT (0),
  [one_star_count] int DEFAULT (0)
)
GO

CREATE TABLE [platforms] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] text UNIQUE NOT NULL
)
GO

CREATE TABLE [game_platforms] (
  [game_id] int,
  [platform_id] int,
  PRIMARY KEY ([game_id], [platform_id])
)
GO

CREATE TABLE [wishlist] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [user_id] int NOT NULL,
  [game_id] int NOT NULL,
  [added_at] datetime DEFAULT (now())
)
GO

EXEC sp_addextendedproperty
@name = N'Column_Description',
@value = '1-10 scale',
@level0type = N'Schema', @level0name = 'dbo',
@level1type = N'Table',  @level1name = 'reviews',
@level2type = N'Column', @level2name = 'rating';
GO

ALTER TABLE [games] ADD FOREIGN KEY ([genre_id]) REFERENCES [genre] ([id])
GO

ALTER TABLE [reviews] ADD FOREIGN KEY ([user_id]) REFERENCES [users] ([id])
GO

ALTER TABLE [reviews] ADD FOREIGN KEY ([game_id]) REFERENCES [games] ([id])
GO

ALTER TABLE [ratings_breakdown] ADD FOREIGN KEY ([game_id]) REFERENCES [games] ([id])
GO

ALTER TABLE [game_platforms] ADD FOREIGN KEY ([game_id]) REFERENCES [games] ([id])
GO

ALTER TABLE [game_platforms] ADD FOREIGN KEY ([platform_id]) REFERENCES [platforms] ([id])
GO

ALTER TABLE [wishlist] ADD FOREIGN KEY ([user_id]) REFERENCES [users] ([id])
GO

ALTER TABLE [wishlist] ADD FOREIGN KEY ([game_id]) REFERENCES [games] ([id])
GO
