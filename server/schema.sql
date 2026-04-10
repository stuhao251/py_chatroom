CREATE DATABASE IF NOT EXISTS python_chatroom DEFAULT CHARACTER SET utf8mb4;
USE python_chatroom;


CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    login_name VARCHAR(20) NOT NULL UNIQUE COMMENT '登录名，只允许数字',
    nickname VARCHAR(50) NOT NULL COMMENT '昵称',
    gender ENUM('男', '女') NOT NULL DEFAULT '男' COMMENT '性别',
    password_hash VARCHAR(128) NOT NULL COMMENT '密码哈希',
    avatar_object_key VARCHAR(255) DEFAULT NULL COMMENT '头像在OSS中的对象路径',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_online TINYINT NOT NULL DEFAULT 0 COMMENT '是否在线：0离线 1在线'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE IF NOT EXISTS friends (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    friend_id INT NOT NULL,
    UNIQUE KEY uniq_friend(user_id, friend_id)
);

CREATE TABLE IF NOT EXISTS chat_groups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_name VARCHAR(100) NOT NULL UNIQUE,
    owner_id INT NOT NULL
);

CREATE TABLE IF NOT EXISTS group_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    UNIQUE KEY uniq_group_member(group_id, user_id)
);