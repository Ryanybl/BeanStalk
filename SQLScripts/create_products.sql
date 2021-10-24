DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` varchar(128) DEFAULT NULL,
  `name` varchar(128) DEFAULT NULL,
  `price` varchar(45) DEFAULT NULL,
  `hash` varchar(45) DEFAULT NULL,
  `content` varchar(128) DEFAULT NULL,
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4;