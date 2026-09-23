-- Quantas assinaturas ativas existem em cada país?

SELECT  pa.nome_pais,
        COUNT(*) AS qtd_assinaturas_ativas
FROM ppgcd_artflix_db.assinatura a
INNER JOIN ppgcd_artflix_db.pais   pa
	ON pa.cod_pais   = a.cod_pais
INNER JOIN ppgcd_artflix_db.status st
	ON st.cod_status = a.cod_status
WHERE st.nome_status = 'Ativa'
GROUP BY pa.nome_pais
ORDER BY qtd_assinaturas_ativas DESC;

-- Qual plano concentra mais assinaturas ativas?

SELECT  pl.nome_plano,
        pl.qtd_telas,
        COUNT(*) AS qtd_assinaturas_ativas,
        COUNT(DISTINCT a.cod_pais) AS qtd_paises_com_assinantes
FROM ppgcd_artflix_db.assinatura a
INNER JOIN ppgcd_artflix_db.plano  pl ON pl.cod_plano  = a.cod_plano
INNER JOIN ppgcd_artflix_db.status st ON st.cod_status = a.cod_status
WHERE st.nome_status = 'Ativa'
GROUP BY pl.nome_plano, pl.qtd_telas
ORDER BY qtd_assinaturas_ativas DESC;

-- Quais os 10 títulos mais assistidos no semestre?

SELECT  t.nome_titulo,
        t.tipo_titulo,
        COUNT(*) AS qtd_sessoes,
        COUNT(DISTINCT s.cod_perfil) AS qtd_perfis_distintos
FROM ppgcd_artflix_db.sessoes s
INNER JOIN ppgcd_artflix_db.titulo t
	ON t.cod_titulo = s.cod_titulo
WHERE s.data_hora_inicio >= '2026-01-01'
  AND s.data_hora_inicio <  '2026-07-01'
GROUP BY t.cod_titulo, t.nome_titulo, t.tipo_titulo
ORDER BY qtd_sessoes DESC
LIMIT 10;


-- Quais gêneros são mais assistidos no Brasil?

SELECT  g.nome_genero,
        COUNT(*) AS qtd_sessoes,
        COUNT(DISTINCT s.cod_titulo) AS qtd_titulos_assistidos
FROM ppgcd_artflix_db.sessoes s
INNER JOIN ppgcd_artflix_db.titulo_genero tg
	ON tg.cod_titulo = s.cod_titulo
INNER JOIN ppgcd_artflix_db.genero g 
	ON g.cod_genero = tg.cod_genero
INNER JOIN pais pa
	ON pa.cod_pais = s.cod_pais
WHERE pa.sigla_iso = 'BR'
GROUP BY g.nome_genero
ORDER BY qtd_sessoes DESC;

-- Por que os assinantes cancelam, em cada plano?

SELECT  pl.nome_plano,
        h.motivo,
        COUNT(*) AS qtd_cancelamentos
FROM ppgcd_artflix_db.historico h
INNER JOIN ppgcd_artflix_db.status st
	ON st.cod_status = h.cod_status
INNER JOIN ppgcd_artflix_db.assinatura a
	ON a.cod_assinatura = h.cod_assinatura
INNER JOIN ppgcd_artflix_db.plano pl
	ON pl.cod_plano = a.cod_plano
WHERE st.nome_status = 'Cancelada'
GROUP BY pl.nome_plano, h.motivo
ORDER BY pl.nome_plano, qtd_cancelamentos DESC;

-- Q6. Quantas cobranças estão em atraso, por país?

SELECT  pa.nome_pais,
        c.moeda,
        COUNT(*) AS qtd_cobrancas_em_atraso,
        COUNT(DISTINCT a.cod_assinante) AS qtd_assinantes_inadimplentes
FROM ppgcd_artflix_db.cobranca c
INNER JOIN ppgcd_artflix_db.assinatura a
	ON a.cod_assinatura = c.cod_assinatura
INNER JOIN ppgcd_artflix_db.pais pa
	ON pa.cod_pais = a.cod_pais
WHERE c.situacao_pagamento = 'Em atraso'
GROUP BY pa.nome_pais, c.moeda
ORDER BY qtd_cobrancas_em_atraso DESC;


-- Em que tipo de dispositivo o público mais assiste?

SELECT  d.tipo_dispositivo,
        COUNT(*) AS qtd_sessoes,
        COUNT(DISTINCT s.cod_perfil) AS qtd_perfis,
        COUNT(DISTINCT s.cod_dispositivo) AS qtd_aparelhos
FROM ppgcd_artflix_db.sessoes s
INNER JOIN ppgcd_artflix_db.dispositivo d
	ON d.cod_dispositivo = s.cod_dispositivo
GROUP BY d.tipo_dispositivo
ORDER BY qtd_sessoes DESC;


-- O que o público procura e não encontra no catálogo?

SELECT  pa.nome_pais,
        pq.termo_pesquisado,
        COUNT(*) AS qtd_buscas_sem_resultado
FROM pesquisa pq
INNER JOIN perfil pf
	ON pf.cod_perfil = pq.cod_perfil
INNER JOIN assinatura a
	ON a.cod_assinatura = pf.cod_assinatura
INNER JOIN pais pa
	ON pa.cod_pais = a.cod_pais
WHERE pq.qtd_resultados = 0
GROUP BY pa.nome_pais, pq.termo_pesquisado
ORDER BY qtd_buscas_sem_resultado DESC
LIMIT 20;


-- Quais contratos de licenciamento vencem nos próximos 90 dias,
--     e quanto do catálogo depende deles?

SELECT  f.nome_fantasia,
        ct.numero_contrato,
        ct.data_fim_vigencia,
        COUNT(*) AS qtd_janelas,
        COUNT(DISTINCT j.cod_titulo) AS qtd_titulos,
        COUNT(DISTINCT j.cod_pais) AS qtd_paises
FROM ppgcd_artflix_db.contrato ct
INNER JOIN ppgcd_artflix_db.fornecedor f
	ON f.cod_fornecedor = ct.cod_fornecedor
INNER JOIN ppgcd_artflix_db.janela j
	ON j.cod_contrato = ct.cod_contrato
WHERE ct.data_fim_vigencia BETWEEN CURDATE()
	AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
GROUP BY f.nome_fantasia, ct.cod_contrato, ct.numero_contrato, ct.data_fim_vigencia
ORDER BY ct.data_fim_vigencia;


-- Quais assinaturas usaram mais aparelhos do que o plano permite (indício de compartilhamento de senha)?

SELECT  a.cod_assinatura,
        pl.nome_plano,
        pl.qtd_telas,
        COUNT(DISTINCT l.cod_dispositivo) AS qtd_dispositivos,
        COUNT(DISTINCT l.endereco_ip) AS qtd_ips,
        COUNT(*) AS qtd_logins
FROM ppgcd_artflix_db.login l
INNER JOIN ppgcd_artflix_db.perfil pf
	ON pf.cod_perfil = l.cod_perfil
INNER JOIN ppgcd_artflix_db.assinatura a
	ON a.cod_assinatura = pf.cod_assinatura
INNER JOIN ppgcd_artflix_db.plano pl
	ON pl.cod_plano = a.cod_plano
WHERE l.data_hora_login >= '2026-06-01'
  AND l.data_hora_login <  '2026-07-01'
GROUP BY a.cod_assinatura, pl.nome_plano, pl.qtd_telas
HAVING COUNT(DISTINCT l.cod_dispositivo) > pl.qtd_telas
ORDER BY qtd_dispositivos DESC;
