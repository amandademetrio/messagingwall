CREATE DATABASE wall_users;

/* Creating a user table */

CREATE TABLE regusers (
  id int(11) NOT NULL AUTO_INCREMENT,
  first_name char(35) NOT NULL DEFAULT '',
  last_name char(35) NOT NULL DEFAULT '',
  email char(255) NOT NULL DEFAULT '',
  password_hash char(255) NOT NULL,
  PRIMARY KEY (id),
  created_at datetime,
  updated_at datetime
) ENGINE=InnoDB AUTO_INCREMENT=4080 DEFAULT CHARSET=latin1;

/* Inserting users into table */

INSERT INTO regusers (first_name,last_name,email,password_hash,created_at,updated_at)
VALUES ("Amanda","Demetrio","amandademetrio@gmail.com","password_hashed",now(),now());

/* Creating messages table */

CREATE TABLE messages (
  id int(11) NOT NULL AUTO_INCREMENT,
  message char(255) NOT NULL DEFAULT '',
  sender_id int NOT NULL,
  receiver_id int NOT NULL,
  PRIMARY KEY (id),
  created_at datetime,
  updated_at datetime
) ENGINE=InnoDB AUTO_INCREMENT=4080 DEFAULT CHARSET=latin1;

/* Inserting values into messages */

INSERT INTO messages (message,sender_id,receiver_id,created_at,updated_at)
VALUES 
("Oi Amanda. Tudo bem por ai?",4081,4080,now(),now()),
("Hey baby! How are you doing today?",4082,4080,now(),now()),
("Hey doll! Are you dolling it up today?",4084,4080,now(),now());

/* Adding user levels */

UPDATE regusers SET user_level=9 WHERE id = 4080;