SET NAMES utf8mb4;
DROP DATABASE IF EXISTS ppgcd_artflix_db;
CREATE DATABASE ppgcd_artflix_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;
USE ppgcd_artflix_db;


CREATE TABLE `ppgcd_artflix_db`.`pais` (
  `cod_pais` INT NOT NULL AUTO_INCREMENT,
  `sigla_iso` CHAR(2) NOT NULL,
  `nome_pais` VARCHAR(60) NOT NULL,
  `moeda_padrao` CHAR(3) NOT NULL,
  `idioma_padrao` VARCHAR(20) NOT NULL,
   PRIMARY KEY (`cod_pais`),
   UNIQUE INDEX `cod_pais_UNIQUE` (`cod_pais` ASC) VISIBLE,
   UNIQUE INDEX `sigla_iso_UNIQUE` (`sigla_iso` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`endereco` (
  `cod_endereco` INT NOT NULL AUTO_INCREMENT,
  `cod_pais` INT NOT NULL,
  `subdivisao` VARCHAR(40) NOT NULL,
  `cidade` VARCHAR(30) NOT NULL,
  `bairro` VARCHAR(40) NOT NULL,
  `logradouro` VARCHAR(60) NOT NULL,
  `codigo_postal` VARCHAR(20) NOT NULL,
   PRIMARY KEY (`cod_endereco`),
  UNIQUE INDEX `cod_endereco_UNIQUE` (`cod_endereco` ASC) VISIBLE,
  CONSTRAINT `fk_endereco_pais`
    FOREIGN KEY (`cod_pais`) REFERENCES `pais` (`cod_pais`)
    ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`assinante` (
  `cod_assinante` INT NOT NULL AUTO_INCREMENT,
  `nome_completo` VARCHAR(128) NOT NULL,
  `cpf_hash` CHAR(128) NOT NULL,     
  `email` CHAR(128) NOT NULL,   
  `senha_hash` CHAR(128) NOT NULL,   
  `salt` CHAR(32) NOT NULL,          
  `telefone` VARCHAR(20) NOT NULL,
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
  UNIQUE INDEX `cpf_hash_UNIQUE` (`cpf_hash` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  CONSTRAINT `fk_assinante_endereco`
    FOREIGN KEY (`cod_endereco`) REFERENCES `endereco` (`cod_endereco`)
    ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE `ppgcd_artflix_db`.`plano` (
  `cod_plano` INT NOT NULL AUTO_INCREMENT,
  `nome_plano` VARCHAR(20),
  `qtd_telas` SMALLINT(2) NOT NULL,
  `resolucao_maxima` VARCHAR(10) NOT NULL,
  `descricao` VARCHAR(60) NOT NULL,
  `indicador_ativo` BOOLEAN NOT NULL,
   PRIMARY KEY (`cod_plano`),
   UNIQUE INDEX `cod_plano_UNIQUE` (`cod_plano` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`plano_pais` (
  `cod_plano_pais` INT NOT NULL AUTO_INCREMENT,
  `cod_plano` INT NOT NULL,
  `cod_pais` INT NOT NULL,
  `preco_mensal` DECIMAL(10,2) NOT NULL,
  `moeda` CHAR(3) NOT NULL,
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
  `nome_status` VARCHAR(30) NOT NULL,
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
  `moeda` CHAR(3) NOT NULL,
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
  `data_hora_status` DATETIME NOT NULL,
  `cod_status` INT NOT NULL,
  `motivo` VARCHAR(60) NULL,
   PRIMARY KEY (`cod_assinatura`,`data_hora_status`),
   CONSTRAINT `fk_historico_assinatura`
     FOREIGN KEY (`cod_assinatura`) REFERENCES `assinatura` (`cod_assinatura`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_historico_status`
     FOREIGN KEY (`cod_status`) REFERENCES `status` (`cod_status`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`classificacao` (
  `cod_classificacao` INT NOT NULL AUTO_INCREMENT,
  `sigla` VARCHAR(4) NOT NULL,
  `idade_minima` SMALLINT NOT NULL,
  `descricao` VARCHAR(80) NULL,
   PRIMARY KEY (`cod_classificacao`),
   UNIQUE INDEX `sigla_UNIQUE` (`sigla` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`genero` (
  `cod_genero` INT NOT NULL AUTO_INCREMENT,
  `nome_genero` VARCHAR(40) NOT NULL,
  `descricao_genero` VARCHAR(120) NULL,
   PRIMARY KEY (`cod_genero`),
   UNIQUE INDEX `nome_genero_UNIQUE` (`nome_genero` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`titulo` (
  `cod_titulo` INT NOT NULL AUTO_INCREMENT,
  `nome_titulo` VARCHAR(120) NOT NULL,
  `tipo_titulo` VARCHAR(20) NOT NULL,
  `ano_lancamento` SMALLINT NOT NULL,
  `duracao_segundos` INT NOT NULL,
  `sinopse` TEXT NULL,
  `idioma_original` VARCHAR(30) NULL,
  `pais_origem` INT NULL,
  `cod_classificacao` INT NOT NULL,
   PRIMARY KEY (`cod_titulo`),
   UNIQUE INDEX `uk_titulo` (`nome_titulo` ASC, `ano_lancamento` ASC) VISIBLE,
   CONSTRAINT `fk_titulo_classificacao`
     FOREIGN KEY (`cod_classificacao`) REFERENCES `classificacao` (`cod_classificacao`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_titulo_pais`
     FOREIGN KEY (`pais_origem`) REFERENCES `pais` (`cod_pais`)
     ON DELETE SET NULL ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`titulo_genero` (
  `cod_titulo` INT NOT NULL,
  `cod_genero` INT NOT NULL,
   PRIMARY KEY (`cod_titulo`,`cod_genero`),
   INDEX `ix_titulo_genero_genero` (`cod_genero` ASC),
   CONSTRAINT `fk_titulo_genero_titulo`
     FOREIGN KEY (`cod_titulo`) REFERENCES `titulo` (`cod_titulo`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_titulo_genero_genero`
     FOREIGN KEY (`cod_genero`) REFERENCES `genero` (`cod_genero`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`perfil` (
  `cod_perfil` INT NOT NULL AUTO_INCREMENT,
  `cod_assinatura` INT NOT NULL,
  `nome_perfil` VARCHAR(40) NOT NULL,
  `data_nascimento` DATE NOT NULL,
  `cod_classificacao` INT NOT NULL,
  `avatar` VARCHAR(60) NULL,
  `indicador_infantil` BOOLEAN NOT NULL DEFAULT FALSE,
  `data_criacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`cod_perfil`),
   UNIQUE INDEX `uk_perfil_nome` (`cod_assinatura` ASC, `nome_perfil` ASC) VISIBLE,
   CONSTRAINT `fk_perfil_assinatura`
     FOREIGN KEY (`cod_assinatura`) REFERENCES `assinatura` (`cod_assinatura`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_perfil_classificacao`
     FOREIGN KEY (`cod_classificacao`) REFERENCES `classificacao` (`cod_classificacao`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`dispositivo` (
  `cod_dispositivo` INT NOT NULL AUTO_INCREMENT,
  `identificador_dispositivo` VARCHAR(80) NOT NULL,
  `tipo_dispositivo` VARCHAR(20) NOT NULL,
  `sistema_operacional` VARCHAR(30) NULL,
  `modelo` VARCHAR(50) NULL,
  `fabricante` VARCHAR(40) NULL,
   PRIMARY KEY (`cod_dispositivo`),
   UNIQUE INDEX `identificador_UNIQUE` (`identificador_dispositivo` ASC) VISIBLE);

CREATE TABLE `ppgcd_artflix_db`.`login` (
  `cod_login` BIGINT NOT NULL AUTO_INCREMENT,
  `cod_perfil` INT NOT NULL,
  `cod_dispositivo` INT NOT NULL,
  `data_hora_login` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `endereco_ip` VARCHAR(45) NOT NULL,
  `latitude` DECIMAL(9,6) NULL,
  `longitude` DECIMAL(9,6) NULL,
  `indicador_gps` BOOLEAN NOT NULL DEFAULT FALSE,
  `data_anonimizacao` DATETIME NULL,
   PRIMARY KEY (`cod_login`),
   INDEX `ix_login_perfil` (`cod_perfil` ASC, `data_hora_login` ASC),
   INDEX `ix_login_dispositivo` (`cod_dispositivo` ASC),
   INDEX `ix_login_retencao` (`data_anonimizacao` ASC, `data_hora_login` ASC),
   CONSTRAINT `fk_login_perfil`
     FOREIGN KEY (`cod_perfil`) REFERENCES `perfil` (`cod_perfil`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_login_dispositivo`
     FOREIGN KEY (`cod_dispositivo`) REFERENCES `dispositivo` (`cod_dispositivo`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`pesquisa` (
  `cod_pesquisa` BIGINT NOT NULL AUTO_INCREMENT,
  `cod_perfil` INT NOT NULL,
  `termo_pesquisado` VARCHAR(120) NOT NULL,
  `data_hora_pesquisa` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `qtd_resultados` INT NOT NULL DEFAULT 0,
  `data_anonimizacao` DATETIME NULL,
   PRIMARY KEY (`cod_pesquisa`),
   INDEX `ix_pesquisa_perfil` (`cod_perfil` ASC, `data_hora_pesquisa` ASC),
   INDEX `ix_pesquisa_termo` (`termo_pesquisado` ASC),
   INDEX `ix_pesquisa_retencao` (`data_anonimizacao` ASC, `data_hora_pesquisa` ASC),
   CONSTRAINT `fk_pesquisa_perfil`
     FOREIGN KEY (`cod_perfil`) REFERENCES `perfil` (`cod_perfil`)
     ON DELETE CASCADE ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`cobranca` (
  `cod_assinatura` INT NOT NULL,
  `competencia` CHAR(7) NOT NULL,
  `valor_cobrado` DECIMAL(10,2) NOT NULL,
  `moeda` CHAR(3) NOT NULL,
  `data_vencimento` DATE NOT NULL,
  `situacao_pagamento` VARCHAR(20) NOT NULL,
  `data_consulta` DATETIME NULL,
   PRIMARY KEY (`cod_assinatura`,`competencia`),
   INDEX `ix_cobranca_situacao` (`situacao_pagamento` ASC, `data_vencimento` ASC),
   CONSTRAINT `fk_cobranca_assinatura`
     FOREIGN KEY (`cod_assinatura`) REFERENCES `assinatura` (`cod_assinatura`)
     ON DELETE CASCADE ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`fornecedor` (
  `cod_fornecedor` INT NOT NULL AUTO_INCREMENT,
  `razao_social` VARCHAR(80) NOT NULL,
  `nome_fantasia` VARCHAR(60) NULL,
  `documento_fiscal` VARCHAR(30) NOT NULL,
  `email_contato` VARCHAR(80) NULL,
  `telefone_contato` VARCHAR(20) NULL,
  `cod_endereco` INT NOT NULL,
   PRIMARY KEY (`cod_fornecedor`),
   UNIQUE INDEX `documento_fiscal_UNIQUE` (`documento_fiscal` ASC) VISIBLE,
   INDEX `ix_fornecedor_endereco` (`cod_endereco` ASC),
   CONSTRAINT `fk_fornecedor_endereco`
     FOREIGN KEY (`cod_endereco`) REFERENCES `endereco` (`cod_endereco`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`contrato` (
  `cod_contrato` INT NOT NULL AUTO_INCREMENT,
  `cod_fornecedor` INT NOT NULL,
  `numero_contrato` VARCHAR(30) NOT NULL,
  `data_assinatura` DATE NOT NULL,
  `data_inicio_vigencia` DATE NOT NULL,
  `data_fim_vigencia` DATE NOT NULL,
  `valor_total` DECIMAL(12,2) NOT NULL,
  `moeda` CHAR(3) NOT NULL,
  `situacao_contrato` VARCHAR(20) NOT NULL,
   PRIMARY KEY (`cod_contrato`),
   UNIQUE INDEX `uk_contrato_numero` (`cod_fornecedor` ASC, `numero_contrato` ASC) VISIBLE,
   CONSTRAINT `fk_contrato_fornecedor`
     FOREIGN KEY (`cod_fornecedor`) REFERENCES `fornecedor` (`cod_fornecedor`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `ck_contrato_vigencia` CHECK (`data_fim_vigencia` > `data_inicio_vigencia`));

CREATE TABLE `ppgcd_artflix_db`.`janela` (
  `cod_janela` INT NOT NULL AUTO_INCREMENT,
  `cod_contrato` INT NOT NULL,
  `cod_titulo` INT NOT NULL,
  `cod_pais` INT NOT NULL,
  `data_inicio` DATE NOT NULL,
  `data_fim` DATE NOT NULL,
  `indicador_exclusividade` BOOLEAN NOT NULL DEFAULT FALSE,
  `valor_licenca` DECIMAL(12,2) NULL,
  `moeda` CHAR(3) NULL,
   PRIMARY KEY (`cod_janela`),
   UNIQUE INDEX `uk_janela` (`cod_contrato` ASC, `cod_titulo` ASC, `cod_pais` ASC) VISIBLE,
   UNIQUE INDEX `uk_janela_sessao` (`cod_janela` ASC, `cod_titulo` ASC, `cod_pais` ASC) VISIBLE,
   INDEX `ix_janela_vigencia` (`cod_titulo` ASC, `cod_pais` ASC,
                               `data_inicio` ASC, `data_fim` ASC),
   CONSTRAINT `fk_janela_contrato`
     FOREIGN KEY (`cod_contrato`) REFERENCES `contrato` (`cod_contrato`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_janela_titulo`
     FOREIGN KEY (`cod_titulo`) REFERENCES `titulo` (`cod_titulo`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_janela_pais`
     FOREIGN KEY (`cod_pais`) REFERENCES `pais` (`cod_pais`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `ck_janela_periodo` CHECK (`data_fim` > `data_inicio`));

CREATE TABLE `ppgcd_artflix_db`.`sessoes` (
  `cod_sessao` BIGINT NOT NULL AUTO_INCREMENT,
  `cod_perfil` INT NOT NULL,
  `cod_titulo` INT NOT NULL,
  `cod_dispositivo` INT NOT NULL,
  `cod_pais` INT NOT NULL,
  `cod_janela` INT NOT NULL,
  `data_hora_inicio` DATETIME NOT NULL,
  `segundos_assistidos` INT NOT NULL,
  `endereco_ip` VARCHAR(45) NOT NULL,
  `data_anonimizacao` DATETIME NULL,
   PRIMARY KEY (`cod_sessao`),
   INDEX `ix_sessao_titulo` (`cod_titulo` ASC, `data_hora_inicio` ASC),
   INDEX `ix_sessao_perfil` (`cod_perfil` ASC, `data_hora_inicio` ASC),
   INDEX `ix_sessao_dispositivo` (`cod_dispositivo` ASC),
   INDEX `ix_sessao_pais` (`cod_pais` ASC),
   INDEX `ix_sessao_janela` (`cod_janela` ASC),
   INDEX `ix_sessao_retencao` (`data_anonimizacao` ASC, `data_hora_inicio` ASC),
   CONSTRAINT `fk_sessao_perfil`
     FOREIGN KEY (`cod_perfil`) REFERENCES `perfil` (`cod_perfil`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_sessao_titulo`
     FOREIGN KEY (`cod_titulo`) REFERENCES `titulo` (`cod_titulo`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_sessao_dispositivo`
     FOREIGN KEY (`cod_dispositivo`) REFERENCES `dispositivo` (`cod_dispositivo`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_sessao_pais`
     FOREIGN KEY (`cod_pais`) REFERENCES `pais` (`cod_pais`)
     ON DELETE RESTRICT ON UPDATE CASCADE,
   CONSTRAINT `fk_sessao_janela`
     FOREIGN KEY (`cod_janela`,`cod_titulo`,`cod_pais`)
     REFERENCES `janela` (`cod_janela`,`cod_titulo`,`cod_pais`)
     ON DELETE RESTRICT ON UPDATE CASCADE);

CREATE TABLE `ppgcd_artflix_db`.`avaliacao` (
  `cod_perfil` INT NOT NULL,
  `cod_titulo` INT NOT NULL,
  `nota` SMALLINT NOT NULL,
  `data_hora_avaliacao` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (`cod_perfil`,`cod_titulo`),
   INDEX `ix_avaliacao_titulo` (`cod_titulo` ASC),
   CONSTRAINT `fk_avaliacao_perfil`
     FOREIGN KEY (`cod_perfil`) REFERENCES `perfil` (`cod_perfil`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `fk_avaliacao_titulo`
     FOREIGN KEY (`cod_titulo`) REFERENCES `titulo` (`cod_titulo`)
     ON DELETE CASCADE ON UPDATE CASCADE,
   CONSTRAINT `ck_avaliacao_nota` CHECK (`nota` BETWEEN 1 AND 5));
