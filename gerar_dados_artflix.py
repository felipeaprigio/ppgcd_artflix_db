import random
from datetime import date, datetime, timedelta

from faker import Faker

# ==========================================================
# CONFIGURACAO
# ==========================================================

SEED = 42

QTD_ASSINANTES = 500
QTD_TITULOS = 300
QTD_DISPOSITIVOS = 400
QTD_FORNECEDORES = 15
QTD_CONTRATOS = 25
QTD_JANELAS = 900
QTD_LOGINS = 20_000
QTD_PESQUISAS = 8_000
QTD_SESSOES = 50_000
QTD_AVALIACOES = 15_000

ARQUIVO_SAIDA = "carga_artflix.sql"
DATA_REFERENCIA = datetime(2026, 9, 1)  # "hoje" do banco
LINHAS_POR_INSERT = 500  # agrupa varias linhas em um INSERT so

# ==========================================================

random.seed(SEED)
fake = Faker("pt_BR")
Faker.seed(SEED)


# ---------- utilitarios de escrita SQL ----------

def lit(valor):
    """Converte um valor Python em literal SQL."""
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, datetime):
        return "'" + valor.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(valor, date):
        return "'" + valor.strftime("%Y-%m-%d") + "'"
    texto = str(valor).replace("\\", "").replace("'", "''")
    return "'" + texto + "'"


def escrever_insert(arq, tabela, colunas, linhas):
    """Escreve os INSERTs de uma tabela em lotes."""
    if not linhas:
        return
    cols = ", ".join("`%s`" % c for c in colunas)
    arq.write("\n-- %s (%d linhas)\n" % (tabela, len(linhas)))
    for ini in range(0, len(linhas), LINHAS_POR_INSERT):
        lote = linhas[ini:ini + LINHAS_POR_INSERT]
        arq.write("INSERT INTO `%s` (%s) VALUES\n" % (tabela, cols))
        valores = [
            "(" + ", ".join(lit(v) for v in linha) + ")"
            for linha in lote
        ]
        arq.write(",\n".join(valores))
        arq.write(";\n")


def data_hora_entre(inicio, fim):
    """Sorteia um datetime entre dois datetimes."""
    delta = int((fim - inicio).total_seconds())
    if delta <= 0:
        return inicio
    return inicio + timedelta(seconds=random.randint(0, delta))


def competencias(inicio, fim):
    """Lista de competencias 'AAAA-MM' entre duas datas."""
    lista = []
    ano, mes = inicio.year, inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        lista.append("%04d-%02d" % (ano, mes))
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return lista


# ==========================================================
# TABELAS DE DOMINIO (dados fixos)
# ==========================================================

PAISES = [
    # sigla, nome, moeda, idioma, subdivisoes
    ("BR", "Brasil", "BRL", "Portugues",
     ["Parana", "Sao Paulo", "Bahia", "Ceara", "Rio Grande do Sul"]),
    ("AR", "Argentina", "ARS", "Espanhol",
     ["Buenos Aires", "Cordoba", "Mendoza", "Santa Fe"]),
    ("CL", "Chile", "CLP", "Espanhol",
     ["Region Metropolitana", "Valparaiso", "Biobio"]),
    ("CO", "Colombia", "COP", "Espanhol",
     ["Cundinamarca", "Antioquia", "Valle del Cauca"]),
    ("MX", "Mexico", "MXN", "Espanhol",
     ["Ciudad de Mexico", "Jalisco", "Nuevo Leon", "Puebla"]),
    ("PE", "Peru", "PEN", "Espanhol",
     ["Lima", "Arequipa", "Cusco"]),
    ("UY", "Uruguai", "UYU", "Espanhol",
     ["Montevideo", "Canelones", "Maldonado"]),
    ("PY", "Paraguai", "PYG", "Espanhol",
     ["Central", "Alto Parana", "Itapua"]),
]

MOEDAS = [
    # codigo ISO 4217, nome, simbolo
    ("ARS", "Peso argentino", "$"),
    ("BRL", "Real brasileiro", "R$"),
    ("CLP", "Peso chileno", "$"),
    ("COP", "Peso colombiano", "$"),
    ("MXN", "Peso mexicano", "$"),
    ("PEN", "Sol peruano", "S/"),
    ("PYG", "Guarani paraguaio", "Gs"),
    ("USD", "Dolar americano", "US$"),
    ("UYU", "Peso uruguaio", "$U"),
]

# moedas aceitas nos contratos de licenciamento
MOEDAS_LICENCIAMENTO = ["BRL", "USD"]

# fator aproximado da moeda em relacao ao real, so para dar precos plausiveis
FATOR_MOEDA = {
    "BRL": 1.0, "ARS": 25.0, "CLP": 180.0, "COP": 800.0,
    "MXN": 3.5, "PEN": 0.75, "UYU": 8.0, "PYG": 1400.0,
}

# taxa aproximada de cada moeda em relacao ao dolar (1 USD = X moeda)
TAXA_USD = {
    "BRL": 5.40, "ARS": 135.0, "CLP": 950.0, "COP": 4200.0,
    "MXN": 18.5, "PEN": 3.80, "UYU": 41.0, "PYG": 7400.0,
    "USD": 1.0,
}

CLASSIFICACOES = [
    ("L", 0, "Livre para todos os publicos"),
    ("10", 10, "Nao recomendado para menores de 10 anos"),
    ("12", 12, "Nao recomendado para menores de 12 anos"),
    ("14", 14, "Nao recomendado para menores de 14 anos"),
    ("16", 16, "Nao recomendado para menores de 16 anos"),
    ("18", 18, "Nao recomendado para menores de 18 anos"),
]

STATUS = [
    ("ATIVA", "Assinatura em vigor e com acesso liberado"),
    ("INADIMPLENTE", "Pagamento em atraso, acesso sob analise"),
    ("SUSPENSA", "Acesso bloqueado temporariamente"),
    ("CANCELADA", "Encerrada a pedido do assinante"),
]

GENEROS = [
    ("Acao", "Perseguicoes, lutas e ritmo acelerado"),
    ("Aventura", "Jornadas e exploracao de lugares novos"),
    ("Comedia", "Narrativa de humor"),
    ("Drama", "Conflitos humanos e emocionais"),
    ("Documentario", "Registro de fatos reais"),
    ("Ficcao Cientifica", "Especulacao cientifica e tecnologica"),
    ("Terror", "Construcao de medo e tensao"),
    ("Suspense", "Tensao narrativa e reviravoltas"),
    ("Romance", "Relacoes afetivas no centro da trama"),
    ("Animacao", "Producao em tecnica de animacao"),
    ("Infantil", "Conteudo voltado ao publico infantil"),
    ("Musical", "Narrativa conduzida por numeros musicais"),
]

PLANOS = [
    ("Basico", 1, "720p", "Uma tela, sem alta definicao", True, 19.90),
    ("Padrao", 2, "1080p", "Duas telas em alta definicao", True, 39.90),
    ("Premium", 4, "4K", "Quatro telas em ultra alta definicao", True, 59.90),
    ("Familia", 5, "4K", "Cinco telas e perfis extras", True, 74.90),
]

TIPOS_DISPOSITIVO = ["SmartTV", "Celular", "Tablet", "Computador", "Console"]
SIS_OPERACIONAIS = ["Android", "iOS", "Windows", "Linux", "tvOS", "WebOS"]
FABRICANTES = ["Samsung", "LG", "Apple", "Motorola", "Sony", "Xiaomi", "Dell"]

PALAVRAS_TITULO_A = [
    "A Ultima", "O Segredo", "Noites de", "O Retorno de", "Cronicas de",
    "Alem de", "A Casa de", "Sombras de", "O Codigo", "Herdeiros de",
    "A Rota", "Ecos de", "O Silencio de", "Filhos de", "A Marca de",
]
PALAVRAS_TITULO_B = [
    "Curitiba", "Ipanema", "Patagonia", "Atacama", "Oaxaca", "Lima",
    "Montevideu", "Manaus", "Bogota", "Cordilheira", "Pampa", "Cerrado",
    "Salvador", "Assuncao", "Valparaiso", "Amazonia", "Andes", "Recife",
]

TERMOS_PESQUISA = [
    "acao", "comedia romantica", "documentario natureza", "series novas",
    "filmes infantis", "terror nacional", "lancamentos 2026", "suspense",
    "animacao", "drama historico", "premiados", "ficcao cientifica",
    "para assistir em familia", "curta duracao", "true crime",
]


# ==========================================================
# GERACAO
# ==========================================================

def main():
    print("Gerando dados com semente %d ..." % SEED)
    arq = open(ARQUIVO_SAIDA, "w", encoding="utf-8")

    arq.write("-- Carga de dados de exemplo do ARTFLIX\n")
    arq.write("-- Gerado por gerar_dados_artflix.py (semente = %d)\n" % SEED)
    arq.write("-- Este arquivo e derivado: nao precisa ir para o GitHub.\n\n")
    arq.write("SET NAMES utf8mb4;\n")
    arq.write("USE `ppgcd_artflix_db`;\n")
    arq.write("SET FOREIGN_KEY_CHECKS = 0;\n")
    arq.write("SET UNIQUE_CHECKS = 0;\n")
    arq.write("SET AUTOCOMMIT = 0;\n")

    # ---------- moeda ----------
    codigos_moeda = {m[0] for m in MOEDAS}
    for sigla, nome, moeda, idioma, subdivs in PAISES:
        assert moeda in codigos_moeda, "moeda %s fora da tabela MOEDA" % moeda
    for moeda in list(FATOR_MOEDA) + list(TAXA_USD) + MOEDAS_LICENCIAMENTO:
        assert moeda in codigos_moeda, "moeda %s fora da tabela MOEDA" % moeda
    escrever_insert(arq, "moeda",
                    ["codigo_moeda", "nome_moeda", "simbolo"], MOEDAS)

    # ---------- pais ----------
    paises = []
    for i, (sigla, nome, moeda, idioma, subdivs) in enumerate(PAISES, start=1):
        paises.append({
            "cod": i, "sigla": sigla, "nome": nome,
            "moeda": moeda, "idioma": idioma, "subdivisoes": subdivs,
        })
    escrever_insert(
        arq, "pais",
        ["cod_pais", "sigla_iso", "nome_pais", "moeda_padrao", "idioma_padrao"],
        [(p["cod"], p["sigla"], p["nome"], p["moeda"], p["idioma"])
         for p in paises],
    )

    # ---------- cotacao ----------
    comps_cotacao = competencias(date(2023, 1, 1), DATA_REFERENCIA.date())
    linhas = []
    for moeda, taxa_base in TAXA_USD.items():
        if moeda == "USD":  # moeda de referencia: paridade fixa
            for comp in comps_cotacao:
                linhas.append((moeda, comp, 1.0, "Paridade"))
            continue
        taxa = taxa_base * random.uniform(0.85, 1.0)
        for comp in comps_cotacao:
            taxa *= random.uniform(0.985, 1.02)  # variacao mensal
            linhas.append((moeda, comp, round(taxa, 10), "Banco Central"))
    escrever_insert(arq, "cotacao",
                    ["moeda", "competencia", "taxa_usd", "fonte"], linhas)

    # ---------- classificacao ----------
    classificacoes = []
    for i, (sigla, idade, desc) in enumerate(CLASSIFICACOES, start=1):
        classificacoes.append({"cod": i, "sigla": sigla, "idade": idade})
    escrever_insert(
        arq, "classificacao",
        ["cod_classificacao", "sigla", "idade_minima", "descricao"],
        [(c[0] + 1, c[1][0], c[1][1], c[1][2])
         for c in enumerate(CLASSIFICACOES)],
    )

    # ---------- status ----------
    status_lista = [{"cod": i, "nome": n}
                    for i, (n, d) in enumerate(STATUS, start=1)]
    escrever_insert(
        arq, "status", ["cod_status", "nome_status", "descricao_status"],
        [(i, n, d) for i, (n, d) in enumerate(STATUS, start=1)],
    )
    cod_ativa = 1
    cod_inadimplente = 2
    cod_suspensa = 3
    cod_cancelada = 4

    # ---------- genero ----------
    escrever_insert(
        arq, "genero", ["cod_genero", "nome_genero", "descricao_genero"],
        [(i, n, d) for i, (n, d) in enumerate(GENEROS, start=1)],
    )

    # ---------- plano ----------
    escrever_insert(
        arq, "plano",
        ["cod_plano", "nome_plano", "qtd_telas", "resolucao_maxima",
         "descricao", "indicador_ativo"],
        [(i, nome, telas, res, desc, ativo)
         for i, (nome, telas, res, desc, ativo, _) in enumerate(PLANOS, start=1)],
    )

    # ---------- plano_pais ----------
    precos = {}  # (cod_plano, cod_pais) -> (preco, moeda)
    linhas = []
    for i, (nome, telas, res, desc, ativo, preco_brl) in enumerate(PLANOS, start=1):
        for p in paises:
            fator = FATOR_MOEDA[p["moeda"]]
            preco = round(preco_brl * fator * random.uniform(0.92, 1.08), 2)
            disponivel = not (nome == "Familia" and p["sigla"] in ("PY", "UY"))
            precos[(i, p["cod"])] = (preco, p["moeda"], disponivel)
            linhas.append((i, p["cod"], preco, p["moeda"], disponivel))
    escrever_insert(
        arq, "plano_pais",
        ["cod_plano", "cod_pais", "preco_mensal", "moeda",
         "indicador_disponibilidade"], linhas,
    )

    # ---------- endereco ----------
    enderecos = []  # (cod_endereco, cod_pais)
    linhas = []
    total_enderecos = QTD_ASSINANTES + QTD_FORNECEDORES
    for cod in range(1, total_enderecos + 1):
        p = random.choice(paises)
        enderecos.append((cod, p["cod"]))
        linhas.append((
            cod, p["cod"], random.choice(p["subdivisoes"]),
            fake.city()[:30], fake.bairro()[:40], fake.street_name()[:60],
            str(random.randint(1, 4999)),
            random.choice([None, "apto %d" % random.randint(11, 180),
                           "casa %d" % random.randint(1, 9), "bloco B"]),
            fake.postcode(),
        ))
    escrever_insert(
        arq, "endereco",
        ["cod_endereco", "cod_pais", "subdivisao", "cidade", "bairro",
         "logradouro", "numero", "complemento", "codigo_postal"], linhas,
    )

    # ---------- assinante ----------
    TIPOS_DOC = {"BR": "CPF", "AR": "DNI", "CL": "RUT", "CO": "CC",
                 "MX": "CURP", "PE": "DNI", "UY": "CI", "PY": "CI"}
    assinantes = []
    linhas = []
    emails_usados = set()
    for cod in range(1, QTD_ASSINANTES + 1):
        cod_endereco, cod_pais = enderecos[cod - 1]
        sigla = next(p["sigla"] for p in paises if p["cod"] == cod_pais)
        nome = fake.name()
        email = "%s%d@%s" % (
            nome.split()[0].lower().replace(".", ""), cod, fake.free_email_domain())
        while email in emails_usados:
            email = "u%d.%s" % (cod, email)
        emails_usados.add(email)

        data_cadastro = data_hora_entre(datetime(2023, 1, 1),
                                        DATA_REFERENCIA - timedelta(days=45))
        # 4% dos assinantes pediram exclusao (LGPD)
        pediu_exclusao = random.random() < 0.04
        data_sol = None
        data_anon = None
        situacao = "ATIVO"
        if pediu_exclusao:
            data_sol = data_hora_entre(data_cadastro, DATA_REFERENCIA)
            situacao = "EXCLUSAO_SOLICITADA"
            # metade ja teve o prazo cumprido
            if random.random() < 0.5:
                data_anon = data_sol + timedelta(days=random.randint(5, 30))
                if data_anon <= DATA_REFERENCIA:
                    situacao = "ANONIMIZADO"
                else:
                    data_anon = None

        assinantes.append({
            "cod": cod, "cod_pais": cod_pais, "cadastro": data_cadastro,
            "anonimizado": data_anon is not None,
        })
        linhas.append((
            cod, nome[:128], TIPOS_DOC[sigla],
            fake.sha256()[:64] + fake.sha256()[:64],  # documento_hash (128)
            email[:128],
            fake.sha256()[:64] + fake.sha256()[:64],  # senha_hash (128)
            fake.md5()[:32],                          # salt (32)
            fake.msisdn()[:20],
            fake.date_of_birth(minimum_age=18, maximum_age=75),
            data_cadastro, cod_endereco, situacao, data_sol, data_anon,
        ))
    escrever_insert(
        arq, "assinante",
        ["cod_assinante", "nome_completo", "tipo_documento", "documento_hash",
         "email", "senha_hash", "salt", "telefone", "data_nascimento",
         "data_cadastro", "cod_endereco", "situacao_cadastro",
         "data_solicitacao_exclusao", "data_anonimizacao"], linhas,
    )

    # ---------- assinatura ----------
    assinaturas = []
    linhas_ass = []
    linhas_hist = []
    linhas_cob = []
    cod_assinatura = 0
    for a in assinantes:
        qtd = 1 if random.random() < 0.9 else 2  # 10% trocaram de plano
        inicio_periodo = a["cadastro"]
        for n in range(qtd):
            # escolhe um plano disponivel no pais do assinante
            candidatos = [cp for cp in precos
                          if cp[1] == a["cod_pais"] and precos[cp][2]]
            cod_plano = random.choice(candidatos)[0]
            preco, moeda, _ = precos[(cod_plano, a["cod_pais"])]

            cod_assinatura += 1
            data_inicio = inicio_periodo
            ultima = (n == qtd - 1)

            if not ultima:
                status_atual = cod_cancelada
                data_cancel = data_hora_entre(
                    data_inicio + timedelta(days=60), DATA_REFERENCIA)
                data_fim = data_cancel + timedelta(days=random.randint(1, 30))
                inicio_periodo = data_cancel
            else:
                sorteio = random.random()
                if sorteio < 0.80:
                    status_atual = cod_ativa
                elif sorteio < 0.90:
                    status_atual = cod_inadimplente
                elif sorteio < 0.95:
                    status_atual = cod_suspensa
                else:
                    status_atual = cod_cancelada
                data_cancel = None
                data_fim = None
                if status_atual == cod_cancelada:
                    data_cancel = data_hora_entre(
                        data_inicio + timedelta(days=60), DATA_REFERENCIA)
                    data_fim = data_cancel + timedelta(days=random.randint(1, 30))

            fim_vigencia = data_cancel or DATA_REFERENCIA
            assinaturas.append({
                "cod": cod_assinatura, "cod_assinante": a["cod"],
                "cod_pais": a["cod_pais"], "inicio": data_inicio,
                "fim": fim_vigencia, "status": status_atual,
                "anonimizado": a["anonimizado"],
                "telas": PLANOS[cod_plano - 1][1],
            })
            dia_venc = random.randint(1, 28)
            linhas_ass.append((
                cod_assinatura, a["cod"], cod_plano, a["cod_pais"],
                data_inicio, dia_venc, preco, moeda, status_atual,
                data_cancel, data_fim,
            ))

            # historico: contratacao + eventual mudanca de status
            linhas_hist.append((cod_assinatura, data_inicio, cod_ativa,
                                "Contratacao"))
            if status_atual != cod_ativa:
                momento = data_cancel or data_hora_entre(
                    data_inicio + timedelta(days=30), DATA_REFERENCIA)
                motivos = {
                    cod_cancelada: "Cancelamento a pedido",
                    cod_inadimplente: "Pagamento nao identificado",
                    cod_suspensa: "Bloqueio por inadimplencia",
                }
                linhas_hist.append((cod_assinatura, momento, status_atual,
                                    motivos[status_atual]))

            # cobranca mensal
            for comp in competencias(data_inicio.date(), fim_vigencia.date()):
                ano, mes = int(comp[:4]), int(comp[5:])
                venc = date(ano, mes, min(dia_venc, 28))
                if random.random() < 0.90:
                    situacao_pg = "EM DIA"
                else:
                    situacao_pg = "EM ATRASO"
                linhas_cob.append((
                    cod_assinatura, comp, preco, moeda, venc, situacao_pg,
                    datetime.combine(venc, datetime.min.time())
                    + timedelta(days=2, hours=random.randint(0, 20)),
                ))

    escrever_insert(
        arq, "assinatura",
        ["cod_assinatura", "cod_assinante", "cod_plano", "cod_pais",
         "data_inicio", "dia_vencimento", "valor_contratado", "moeda",
         "cod_status", "data_cancelamento", "data_fim_acesso"], linhas_ass,
    )
    escrever_insert(
        arq, "historico",
        ["cod_assinatura", "data_hora_status", "cod_status", "motivo"],
        linhas_hist,
    )
    escrever_insert(
        arq, "cobranca",
        ["cod_assinatura", "competencia", "valor_cobrado", "moeda",
         "data_vencimento", "situacao_pagamento", "data_consulta"], linhas_cob,
    )

    # ---------- perfil ----------
    NOMES_PERFIL = ["Principal", "Infantil", "Visitante", "Sala", "Quarto",
                    "Familia", "Trabalho", "Fim de semana"]
    perfis = []
    linhas = []
    cod_perfil = 0
    for ass in assinaturas:
        qtd_perfis = min(random.randint(1, 5), ass["telas"] + 1, 5)
        nomes = random.sample(NOMES_PERFIL, qtd_perfis)
        for nome_p in nomes:
            cod_perfil += 1
            infantil = (nome_p == "Infantil") or random.random() < 0.15
            if infantil:
                nascimento = fake.date_of_birth(minimum_age=4, maximum_age=12)
                idade = (DATA_REFERENCIA.date() - nascimento).days // 365
                cod_class = 1 if idade < 10 else 2
            else:
                nascimento = fake.date_of_birth(minimum_age=14, maximum_age=70)
                idade = (DATA_REFERENCIA.date() - nascimento).days // 365
                cod_class = 6 if idade >= 18 else random.choice([3, 4, 5])
            criacao = data_hora_entre(ass["inicio"], ass["fim"])
            perfis.append({
                "cod": cod_perfil, "cod_pais": ass["cod_pais"],
                "limite": CLASSIFICACOES[cod_class - 1][1],
                "criacao": criacao, "fim": ass["fim"],
                "anonimizado": ass["anonimizado"],
            })
            linhas.append((
                cod_perfil, ass["cod"], nome_p, nascimento, cod_class,
                "avatar_%02d.png" % random.randint(1, 20), infantil, criacao,
            ))
    escrever_insert(
        arq, "perfil",
        ["cod_perfil", "cod_assinatura", "nome_perfil", "data_nascimento",
         "cod_classificacao", "avatar", "indicador_infantil", "data_criacao"],
        linhas,
    )

    # ---------- dispositivo ----------
    linhas = []
    for cod in range(1, QTD_DISPOSITIVOS + 1):
        tipo = random.choice(TIPOS_DISPOSITIVO)
        linhas.append((
            cod, fake.uuid4(), tipo, random.choice(SIS_OPERACIONAIS),
            "%s %d" % (random.choice(["Serie", "Modelo", "Linha"]),
                       random.randint(1, 40)),
            random.choice(FABRICANTES),
        ))
    escrever_insert(
        arq, "dispositivo",
        ["cod_dispositivo", "identificador_dispositivo", "tipo_dispositivo",
         "sistema_operacional", "modelo", "fabricante"], linhas,
    )

    # ---------- titulo ----------
    titulos = []
    linhas = []
    nomes_usados = set()
    for cod in range(1, QTD_TITULOS + 1):
        tipo = random.choices(["FILME", "SERIE", "DOCUMENTARIO"],
                              weights=[55, 35, 10])[0]
        nome = "%s %s" % (random.choice(PALAVRAS_TITULO_A),
                          random.choice(PALAVRAS_TITULO_B))
        ano = random.randint(1995, 2026)
        while (nome, ano) in nomes_usados:
            nome = "%s %s II" % (random.choice(PALAVRAS_TITULO_A),
                                 random.choice(PALAVRAS_TITULO_B))
            ano = random.randint(1995, 2026)
        nomes_usados.add((nome, ano))

        if tipo == "SERIE":
            duracao = random.randint(1200, 3000)
        elif tipo == "DOCUMENTARIO":
            duracao = random.randint(2700, 6000)
        else:
            duracao = random.randint(4500, 10800)

        cod_class = random.choices([1, 2, 3, 4, 5, 6],
                                   weights=[20, 15, 20, 15, 15, 15])[0]
        pais_origem = random.choice(paises)["cod"]
        titulos.append({"cod": cod, "duracao": duracao, "classe": cod_class,
                        "idade": CLASSIFICACOES[cod_class - 1][1], "ano": ano})
        linhas.append((
            cod, nome, tipo, ano, duracao,
            fake.sentence(nb_words=18)[:400],
            random.choice(["Portugues", "Espanhol", "Ingles"]),
            pais_origem, cod_class,
        ))
    escrever_insert(
        arq, "titulo",
        ["cod_titulo", "nome_titulo", "tipo_titulo", "ano_lancamento",
         "duracao_segundos", "sinopse", "idioma_original", "pais_origem",
         "cod_classificacao"], linhas,
    )

    # ---------- titulo_genero (N:N) ----------
    linhas = []
    for t in titulos:
        for cod_gen in random.sample(range(1, len(GENEROS) + 1),
                                     random.randint(1, 3)):
            linhas.append((t["cod"], cod_gen))
    escrever_insert(arq, "titulo_genero", ["cod_titulo", "cod_genero"], linhas)

    # ---------- fornecedor ----------
    linhas = []
    for cod in range(1, QTD_FORNECEDORES + 1):
        cod_endereco = QTD_ASSINANTES + cod
        razao = fake.company()
        linhas.append((
            cod, razao[:80], razao.split()[0][:60], fake.cnpj(),
            "contato@%s" % fake.domain_name(), fake.msisdn()[:20], cod_endereco,
        ))
    escrever_insert(
        arq, "fornecedor",
        ["cod_fornecedor", "razao_social", "nome_fantasia", "documento_fiscal",
         "email_contato", "telefone_contato", "cod_endereco"], linhas,
    )

    # ---------- contrato ----------
    contratos = []
    linhas = []
    for cod in range(1, QTD_CONTRATOS + 1):
        cod_forn = random.randint(1, QTD_FORNECEDORES)
        assinatura_ct = fake.date_between(date(2022, 1, 1), date(2025, 6, 30))
        inicio = assinatura_ct + timedelta(days=random.randint(5, 60))
        fim = inicio + timedelta(days=random.randint(365, 1460))
        contratos.append({"cod": cod, "inicio": inicio, "fim": fim})
        situacao = "VIGENTE" if fim >= DATA_REFERENCIA.date() else "ENCERRADO"
        linhas.append((
            cod, cod_forn, "CT-%04d/%d" % (cod, assinatura_ct.year),
            assinatura_ct, inicio, fim,
            round(random.uniform(150_000, 4_000_000), 2),
            random.choice(MOEDAS_LICENCIAMENTO), situacao,
        ))
    escrever_insert(
        arq, "contrato",
        ["cod_contrato", "cod_fornecedor", "numero_contrato", "data_assinatura",
         "data_inicio_vigencia", "data_fim_vigencia", "valor_total", "moeda",
         "situacao_contrato"], linhas,
    )

    # ---------- janela ----------
    janelas = []
    linhas = []
    chaves = set()
    cod_janela = 0
    tentativas = 0
    while len(janelas) < QTD_JANELAS and tentativas < QTD_JANELAS * 20:
        tentativas += 1
        ct = random.choice(contratos)
        t = random.choice(titulos)
        p = random.choice(paises)
        inicio = ct["inicio"] + timedelta(days=random.randint(0, 200))
        if inicio >= ct["fim"]:
            continue
        chave = (ct["cod"], t["cod"], p["cod"], inicio)
        if chave in chaves:
            continue
        chaves.add(chave)
        fim = min(inicio + timedelta(days=random.randint(180, 1095)), ct["fim"])
        if fim <= inicio:
            continue
        cod_janela += 1
        moeda_lic = random.choice(MOEDAS_LICENCIAMENTO)
        janelas.append({
            "cod": cod_janela, "titulo": t["cod"], "pais": p["cod"],
            "inicio": inicio, "fim": fim, "idade": t["idade"],
            "duracao": t["duracao"],
        })
        linhas.append((
            cod_janela, ct["cod"], t["cod"], p["cod"], inicio, fim,
            random.random() < 0.2,
            round(random.uniform(5_000, 300_000), 2), moeda_lic,
        ))
    escrever_insert(
        arq, "janela",
        ["cod_janela", "cod_contrato", "cod_titulo", "cod_pais", "data_inicio",
         "data_fim", "indicador_exclusividade", "valor_licenca", "moeda"],
        linhas,
    )

    # indexa janelas por pais e faixa etaria (para respeitar a classificacao)
    janelas_por_pais = {}
    for j in janelas:
        janelas_por_pais.setdefault(j["pais"], []).append(j)

    perfis_por_pais = {}
    for pf in perfis:
        perfis_por_pais.setdefault(pf["cod_pais"], []).append(pf)

    paises_com_dados = [c for c in janelas_por_pais if c in perfis_por_pais]

    # ---------- login ----------
    linhas = []
    for cod in range(1, QTD_LOGINS + 1):
        pf = random.choice(perfis)
        momento = data_hora_entre(pf["criacao"], max(pf["fim"], pf["criacao"]))
        tem_gps = random.random() < 0.35
        lat = lon = None
        if tem_gps:
            lat = round(random.uniform(-34.0, 20.0), 6)
            lon = round(random.uniform(-75.0, -35.0), 6)
        # dado sensivel de perfil anonimizado ja foi tratado
        anon = None
        if pf["anonimizado"] or momento < DATA_REFERENCIA - timedelta(days=730):
            if random.random() < 0.6:
                anon = momento + timedelta(days=random.randint(730, 760))
                if anon > DATA_REFERENCIA:
                    anon = None
        linhas.append((cod, pf["cod"], random.randint(1, QTD_DISPOSITIVOS),
                       momento, fake.ipv4(), lat, lon, tem_gps, anon))
    escrever_insert(
        arq, "login",
        ["cod_login", "cod_perfil", "cod_dispositivo", "data_hora_login",
         "endereco_ip", "latitude", "longitude", "indicador_gps",
         "data_anonimizacao"], linhas,
    )

    # ---------- pesquisa ----------
    linhas = []
    for cod in range(1, QTD_PESQUISAS + 1):
        pf = random.choice(perfis)
        momento = data_hora_entre(pf["criacao"], max(pf["fim"], pf["criacao"]))
        linhas.append((cod, pf["cod"], random.choice(TERMOS_PESQUISA), momento,
                       random.randint(0, 60), None))
    escrever_insert(
        arq, "pesquisa",
        ["cod_pesquisa", "cod_perfil", "termo_pesquisado", "data_hora_pesquisa",
         "qtd_resultados", "data_anonimizacao"], linhas,
    )

    # ---------- sessoes ----------
    linhas = []
    cod_sessao = 0
    tentativas = 0
    limite = QTD_SESSOES * 30
    while cod_sessao < QTD_SESSOES and tentativas < limite:
        tentativas += 1
        cod_pais = random.choice(paises_com_dados)
        pf = random.choice(perfis_por_pais[cod_pais])
        j = random.choice(janelas_por_pais[cod_pais])

        # regra: classificacao do titulo <= limite do perfil
        if j["idade"] > pf["limite"]:
            continue

        # regra: sessao dentro da janela vigente e da vida do perfil
        ini = max(datetime.combine(j["inicio"], datetime.min.time()),
                  pf["criacao"])
        fim = min(datetime.combine(j["fim"], datetime.min.time()),
                  pf["fim"], DATA_REFERENCIA)
        if fim <= ini:
            continue

        momento = data_hora_entre(ini, fim)
        # regra: sessao so conta acima de 60 segundos
        assistido = random.randint(61, j["duracao"])
        anon = None
        if pf["anonimizado"]:
            anon = momento + timedelta(days=random.randint(400, 700))
            if anon > DATA_REFERENCIA:
                anon = None

        cod_sessao += 1
        linhas.append((cod_sessao, pf["cod"], j["titulo"],
                       random.randint(1, QTD_DISPOSITIVOS), cod_pais, j["cod"],
                       momento, assistido, fake.ipv4(), anon))
    escrever_insert(
        arq, "sessoes",
        ["cod_sessao", "cod_perfil", "cod_titulo", "cod_dispositivo",
         "cod_pais", "cod_janela", "data_hora_inicio", "segundos_assistidos",
         "endereco_ip", "data_anonimizacao"], linhas,
    )
    print("  sessoes geradas: %d" % cod_sessao)

    # ---------- avaliacao ----------
    linhas = []
    pares = set()
    tentativas = 0
    while len(pares) < QTD_AVALIACOES and tentativas < QTD_AVALIACOES * 20:
        tentativas += 1
        cod_pais = random.choice(paises_com_dados)
        pf = random.choice(perfis_por_pais[cod_pais])
        j = random.choice(janelas_por_pais[cod_pais])
        if j["idade"] > pf["limite"]:
            continue
        par = (pf["cod"], j["titulo"])
        if par in pares:
            continue
        pares.add(par)
        momento = data_hora_entre(pf["criacao"],
                                  min(pf["fim"], DATA_REFERENCIA))
        nota = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 25, 35, 25])[0]
        linhas.append((par[0], par[1], nota, momento))
    escrever_insert(
        arq, "avaliacao",
        ["cod_perfil", "cod_titulo", "nota", "data_hora_avaliacao"], linhas,
    )
    print("  avaliacoes geradas: %d" % len(pares))

    arq.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
    arq.write("SET UNIQUE_CHECKS = 1;\n")
    arq.write("COMMIT;\n")
    arq.close()

    import os
    tamanho = os.path.getsize(ARQUIVO_SAIDA) / (1024 * 1024)
    print("Pronto: %s (%.1f MB)" % (ARQUIVO_SAIDA, tamanho))


if __name__ == "__main__":
    main()
