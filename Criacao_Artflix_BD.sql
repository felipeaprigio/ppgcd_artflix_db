SET NAMES utf8mb4;
CREATE DATABASE ppgcd_artflix_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE ppgcd_artflix_db;


CREATE TABLE `ppgcd_artflix_db`.`pais` (
  `cod_pais` INT NOT NULL AUTO_INCREMENT,
  `sigla_iso` CHAR(2) NOT NULL,
  `nome_pais` VARCHAR(20) NOT NULL,
  `moeda_padrao` VARCHAR(30) NOT NULL,
  `idioma_padrao` VARCHAR(20) NOT NULL,
   PRIMARY KEY (`cod_pais`),
   UNIQUE INDEX `cod_pais_UNIQUE` (`cod_pais` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`endereco` (
  `cod_endereco` INT NOT NULL AUTO_INCREMENT,
  `cod_pais` INT NOT NULL,
  `subdivisao` VARCHAR(20) NOT NULL,
  `cidade` VARCHAR(30) NOT NULL,
  `bairro` VARCHAR(20) NOT NULL,
  `logradouro` VARCHAR(20) NOT NULL,
  `codigo_postal` VARCHAR(20) NOT NULL,
   PRIMARY KEY (`cod_endereco`),
  UNIQUE INDEX `cod_endereco_UNIQUE` (`cod_endereco` ASC) VISIBLE,
  CONSTRAINT `fk_endereco_pais`
    FOREIGN KEY (`cod_pais`) REFERENCES `pais` (`cod_pais`)
    ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`assinante` (
  `cod_assinante` INT NOT NULL AUTO_INCREMENT,
  `nome_completo` VARCHAR(128) NOT NULL,
  `cpf` VARCHAR(128) NOT NULL,
  `email` VARCHAR(128) NOT NULL,
  `telefone` VARCHAR(128) NOT NULL,
  `data_nascimento` DATE NOT NULL,
  `data_cadastro` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cod_endereco` INT NOT NULL,
  `numero` VARCHAR(10) NOT NULL,
  `complemento` VARCHAR(30) NULL,
  `situacao_cadastro` VARCHAR(20) NULL,
  `data_solicitacao_exclusao` DATETIME NULL,
  `data_anonimizacao` DATETIME NULL,
    PRIMARY KEY (`cod_assinante`),
  UNIQUE INDEX `cod_assinante_UNIQUE` (`cod_assinante` ASC) VISIBLE,
  UNIQUE INDEX `cpf_UNIQUE` (`cpf` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  CONSTRAINT `fk_assinante_endereco`
    FOREIGN KEY (`cod_endereco`) REFERENCES `endereco` (`cod_endereco`)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE `ppgcd_artflix_db`.`plano` (
  `cod_plano` INT NOT NULL AUTO_INCREMENT,
  `nome_plano` VARCHAR(20),
  `qtd_telas` SMALLINT(2) NOT NULL,
  `resolucao_maxima` VARCHAR(6) NOT NULL,
  `descricao` VARCHAR(60) NOT NULL,
  `indicador_ativo` BOOLEAN NOT NULL,
   PRIMARY KEY (`cod_plano`),
   UNIQUE INDEX `cod_plano_UNIQUE` (`cod_plano` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`plano_pais` (
  `cod_plano_pais` INT NOT NULL AUTO_INCREMENT,
  `cod_plano` INT NOT NULL,
  `cod_pais` INT NOT NULL,
  `preco_mensal` DECIMAL(10,2) NOT NULL,
  `moeda` VARCHAR(20) NOT NULL,
  `indicador_disponibilidade` BOOLEAN NOT NULL,
   PRIMARY KEY (`cod_plano_pais`),
   UNIQUE INDEX `cod_plano_pais_UNIQUE` (`cod_plano_pais` ASC) VISIBLE,
   UNIQUE INDEX `uk_plano_pais` (`cod_plano` ASC, `cod_pais` ASC) VISIBLE,
   CONSTRAINT `fk_plano_pais_plano`
     FOREIGN KEY (`cod_plano`) REFERENCES `plano` (`cod_plano`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_plano_pais_pais`
     FOREIGN KEY (`cod_pais`) REFERENCES `pais` (`cod_pais`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`status` (
  `cod_status` INT NOT NULL AUTO_INCREMENT,
  `nome_status` VARCHAR(10) NOT NULL,
  `descricao_status` VARCHAR(60) NOT NULL,
   PRIMARY KEY (`cod_status`),
   UNIQUE INDEX `cod_status_UNIQUE` (`cod_status` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`assinatura` (
  `cod_assinatura` INT NOT NULL AUTO_INCREMENT,
  `cod_assinante` INT NOT NULL,
  `cod_plano` INT NOT NULL,
  `data_inicio` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `data_vencimento` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `valor_contratado` DECIMAL(10,2) NOT NULL,
  `moeda` VARCHAR(20) NOT NULL,
  `cod_status` INT NOT NULL,
  `data_cancelamento` DATETIME NULL,
  `data_fim_acesso` DATETIME NULL,
   PRIMARY KEY (`cod_assinatura`),
   UNIQUE INDEX `cod_assinatura_UNIQUE` (`cod_assinatura` ASC) VISIBLE,
   CONSTRAINT `fk_assinatura_assinante`
     FOREIGN KEY (`cod_assinante`) REFERENCES `assinante` (`cod_assinante`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_assinatura_plano`
     FOREIGN KEY (`cod_plano`) REFERENCES `plano` (`cod_plano`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_assinatura_status`
     FOREIGN KEY (`cod_status`) REFERENCES `status` (`cod_status`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`historico` (
  `cod_assinatura` INT NOT NULL,
  `data_hora_status` DATETIME NOT NULL,   -- [5] era VARCHAR(10): nao cabe data e hora
  `cod_status` INT NOT NULL,
  `motivo` VARCHAR(60) NOT NULL,
   PRIMARY KEY (`cod_assinatura`,`data_hora_status`),
   CONSTRAINT `fk_historico_assinatura`
     FOREIGN KEY (`cod_assinatura`) REFERENCES `assinatura` (`cod_assinatura`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_historico_status`
     FOREIGN KEY (`cod_status`) REFERENCES `status` (`cod_status`)
     ON DELETE RESTRICT ON UPDATE CASCADE);