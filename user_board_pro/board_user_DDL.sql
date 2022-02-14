-- user_board_pro.user_table definition

CREATE TABLE `user_table` (
  `userNo` int NOT NULL AUTO_INCREMENT COMMENT '회원 PK',
  `userId` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '회원 id UK',
  `userName` varchar(50) NOT NULL COMMENT '회원 이름',
  `userPwd` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '회원 비밀번호',
  `userBirth` datetime DEFAULT NULL COMMENT '회원 생년월일 YYYYMMDD',
  `userPhone` char(11) DEFAULT NULL COMMENT '회원 연락처 (-)제외',
  `userGender` enum('M','F') CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '회원 성별 (M, F)',
  `userEmail` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '회원 이메일',
  `refreshToken` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '회원 refresh 토큰값',
  `disabled` int NOT NULL DEFAULT '0' COMMENT '사용 중 :0, 삭제 처리 : 1',
  `createdDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '최초 만든 날짜',
  `updatedDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정날짜',
  PRIMARY KEY (`userNo`),
  UNIQUE KEY `userId_UNIQUE` (`userId`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='회원- id, 이름, 비밀번호, 이메일, 연락처, 성별, 토큰';


-- user_board_pro.board_table definition

CREATE TABLE `board_table` (
  `boardNo` int NOT NULL AUTO_INCREMENT COMMENT '작성글 pk',
  `userNo` int DEFAULT NULL COMMENT '회원 정보 (fk_user_userNo)',
  `title` varchar(100) NOT NULL COMMENT '제목',
  `contents` text NOT NULL COMMENT '작성 내용',
  `counting` int NOT NULL DEFAULT '0' COMMENT '조회수',
  `disabled` int NOT NULL DEFAULT '0' COMMENT '사용 중 : 0 / 삭제 처리 : 1',
  `createdDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '최초 만든 날짜',
  `updatedDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정한 날짜',
  PRIMARY KEY (`boardNo`),
  KEY `fk_user_userNo_board_userNo` (`userNo`),
  CONSTRAINT `fk_user_userNo_board_userNo` FOREIGN KEY (`userNo`) REFERENCES `user_table` (`userNo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='게시판 - 작성자, 제목, 내용';

-- user_board_pro.file_table definition

CREATE TABLE `file_table` (
  `fileNo` int NOT NULL AUTO_INCREMENT COMMENT '파일no pk',
  `boardNo` int DEFAULT NULL COMMENT '게시글no fk(fk_board_boardNo)',
  `fileName` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '파일 이름 uuid4',
  `fileNameOrigin` varchar(255) NOT NULL COMMENT 'origin 파일 이름',
  `contentType` varchar(255) NOT NULL COMMENT '파일 type',
  `fileSize` int DEFAULT NULL COMMENT '파일 크기(단위 : byte)',
  `fileFullPath` varchar(500) NOT NULL COMMENT '파일 경로',
  `disabled` int NOT NULL DEFAULT '0' COMMENT '사용 중 : 0 / 삭제 처리 : 1',
  `createdDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '최초 만든 날짜',
  `updatedDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정한 날짜',
  PRIMARY KEY (`fileNo`),
  KEY `fk_board_boardNo_file_boardNo` (`boardNo`),
  CONSTRAINT `fk_board_boardNo_file_boardNo` FOREIGN KEY (`boardNo`) REFERENCES `board_table` (`boardNo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='파일 - 이름, 오리지날 이름, 타입, 크기, 경로';


