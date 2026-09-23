import calendar
import random
from datetime import date, datetime, time, timedelta

from faker import Faker

# CONFIGURACAO

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

# regras de LGPD do negocio
PRAZO_ANONIMIZACAO_DIAS = 15   # apos o pedido de exclusao do titular
RETENCAO_CONSUMO_MESES = 24    # consumo deixa de ser identificavel
HORA_ROTINA_ANONIMIZACAO = time(0, 0, 0)  # rotina diaria, a meia-noite

# tabelas na ordem em que sao carregadas; a limpeza roda na ordem inversa
TABELAS = [
    "moeda", "pais", "cotacao", "classificacao", "status", "genero",
    "plano", "plano_pais", "endereco", "assinante", "assinatura",
    "historico", "cobranca", "perfil", "dispositivo", "titulo",
    "titulo_genero", "fornecedor", "contrato", "janela", "login",
    "pesquisa", "sessoes", "avaliacao",
]

# cada tabela e montada em memoria e escrita no fim, na ordem de TABELAS
SAIDA = {}

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


def guardar(tabela, colunas, linhas):
    """Guarda as linhas de uma tabela para escrita posterior."""
    SAIDA[tabela] = (colunas, linhas)


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


# ---------- utilitarios de data ----------

def data_hora_entre(inicio, fim):
    """Sorteia um datetime entre dois datetimes."""
    delta = int((fim - inicio).total_seconds())
    if delta <= 0:
        return inicio
    return inicio + timedelta(seconds=random.randint(0, delta))


def somar_meses(d, n):
    """Soma n meses a uma date/datetime, ajustando o fim de mes."""
    ano = d.year + (d.month - 1 + n) // 12
    mes = (d.month - 1 + n) % 12 + 1
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return d.replace(year=ano, month=mes, day=dia)


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


def vencimentos(inicio, dia, limite):
    """Datas de vencimento (dia fixo do mes) entre inicio e limite."""
    d = date(inicio.year, inicio.month, dia)
    if d < inicio:
        d = somar_meses(d, 1)
    lista = []
    while d <= limite:
        lista.append(d)
        d = somar_meses(d, 1)
    return lista


def proximo_vencimento(momento, dia):
    """Primeiro vencimento estritamente depois de um momento."""
    d = date(momento.year, momento.month, dia)
    if d <= momento.date():
        d = somar_meses(d, 1)
    return d


# ---------- utilitarios de LGPD ----------

def data_retencao(momento):
    """Quando um registro de consumo completa 24 meses (rotina diaria)."""
    limite = somar_meses(momento, RETENCAO_CONSUMO_MESES)
    return datetime.combine(limite.date() + timedelta(days=1),
                            HORA_ROTINA_ANONIMIZACAO)


def anonimizacao_consumo(momento, anon_titular):
    """Data de anonimizacao de um registro de consumo, ou None.

    Vale a primeira que ocorrer ate a data de referencia:
    - o registro completou 24 meses;
    - o titular pediu exclusao e foi anonimizado.
    """
    candidatas = []
    retencao = data_retencao(momento)
    if retencao <= DATA_REFERENCIA:
        candidatas.append(retencao)
    if anon_titular is not None:
        candidatas.append(max(anon_titular, momento))
    return min(candidatas) if candidatas else None


def mascarar_ip(ip):
    """Zera o ultimo octeto do IPv4 (deixa de identificar o domicilio)."""
    return ip.rsplit(".", 1)[0] + ".0"


# TABELAS DE DOMINIO (dados fixos)

PAISES = [
    # sigla, nome, moeda, idioma, subdivisoes, centro GPS (lat, lon, raio)
    ("BR", "Brasil", "BRL", "Portugues",
     ["Parana", "Sao Paulo", "Bahia", "Ceara", "Rio Grande do Sul"],
     (-15.8, -47.9, 6.0)),
    ("AR", "Argentina", "ARS", "Espanhol",
     ["Buenos Aires", "Cordoba", "Mendoza", "Santa Fe"],
     (-34.6, -58.4, 3.0)),
    ("CL", "Chile", "CLP", "Espanhol",
     ["Region Metropolitana", "Valparaiso", "Biobio"],
     (-33.4, -70.6, 2.0)),
    ("CO", "Colombia", "COP", "Espanhol",
     ["Cundinamarca", "Antioquia", "Valle del Cauca"],
     (4.7, -74.1, 2.5)),
    ("MX", "Mexico", "MXN", "Espanhol",
     ["Ciudad de Mexico", "Jalisco", "Nuevo Leon", "Puebla"],
     (19.4, -99.1, 3.0)),
    ("PE", "Peru", "PEN", "Espanhol",
     ["Lima", "Arequipa", "Cusco"],
     (-12.0, -77.0, 2.5)),
    ("UY", "Uruguai", "UYU", "Espanhol",
     ["Montevideo", "Canelones", "Maldonado"],
     (-34.9, -56.2, 0.8)),
    ("PY", "Paraguai", "PYG", "Espanhol",
     ["Central", "Alto Parana", "Itapua"],
     (-25.3, -57.6, 1.5)),
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

# o acervo so tem obras unicas: filmes e documentarios (sem series)
TIPOS_TITULO = ["FILME", "DOCUMENTARIO"]
PESOS_TIPO_TITULO = [85, 15]

# combinacoes coerentes de tipo, sistema operacional e fabricante
DISPOSITIVOS = {
    "Celular": [("Android", ["Samsung", "Motorola", "Xiaomi"]),
                ("iOS", ["Apple"])],
    "Tablet": [("Android", ["Samsung", "Xiaomi"]), ("iPadOS", ["Apple"])],
    "Computador": [("Windows", ["Dell", "Samsung", "LG"]),
                   ("Linux", ["Dell"]), ("macOS", ["Apple"])],
    "SmartTV": [("WebOS", ["LG"]), ("Tizen", ["Samsung"]),
                ("Android TV", ["Sony", "Xiaomi"]), ("tvOS", ["Apple"])],
    "Console": [("PlayStation OS", ["Sony"]), ("Xbox OS", ["Microsoft"])],
}
# so estes tipos tem GPS integrado
TIPOS_COM_GPS = {"Celular", "Tablet"}

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
    "acao", "comedia romantica", "documentario natureza", "filmes nacionais",
    "filmes infantis", "terror nacional", "lancamentos 2026", "suspense",
    "animacao", "drama historico", "premiados", "ficcao cientifica",
    "para assistir em familia", "curta duracao", "true crime",
]

TEXTO_ANONIMO = "ANONIMIZADO"


# GERACAO

def main():
    print("Gerando dados com semente %d ..." % SEED)

    cod_ativa = 1
    cod_inadimplente = 2
    cod_suspensa = 3
    cod_cancelada = 4

    # ---------- moeda ----------
    codigos_moeda = {m[0] for m in MOEDAS}
    for pais in PAISES:
        assert pais[2] in codigos_moeda, "moeda %s fora da tabela MOEDA" % pais[2]
    for moeda in list(FATOR_MOEDA) + list(TAXA_USD) + MOEDAS_LICENCIAMENTO:
        assert moeda in codigos_moeda, "moeda %s fora da tabela MOEDA" % moeda
    guardar("moeda", ["codigo_moeda", "nome_moeda", "simbolo"], MOEDAS)

    # ---------- pais ----------
    paises = []
    for i, (sigla, nome, moeda, idioma, subdivs, gps) in enumerate(PAISES, start=1):
        paises.append({
            "cod": i, "sigla": sigla, "nome": nome, "moeda": moeda,
            "idioma": idioma, "subdivisoes": subdivs, "gps": gps,
        })
    pais_por_cod = {p["cod"]: p for p in paises}
    guardar(
        "pais",
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
    guardar("cotacao", ["moeda", "competencia", "taxa_usd", "fonte"], linhas)

    # ---------- classificacao ----------
    guardar(
        "classificacao",
        ["cod_classificacao", "sigla", "idade_minima", "descricao"],
        [(i, s, idade, d)
         for i, (s, idade, d) in enumerate(CLASSIFICACOES, start=1)],
    )

    # ---------- status ----------
    guardar(
        "status", ["cod_status", "nome_status", "descricao_status"],
        [(i, n, d) for i, (n, d) in enumerate(STATUS, start=1)],
    )

    # ---------- genero ----------
    guardar(
        "genero", ["cod_genero", "nome_genero", "descricao_genero"],
        [(i, n, d) for i, (n, d) in enumerate(GENEROS, start=1)],
    )

    # ---------- plano ----------
    guardar(
        "plano",
        ["cod_plano", "nome_plano", "qtd_telas", "resolucao_maxima",
         "descricao", "indicador_ativo"],
        [(i, nome, telas, res, desc, ativo)
         for i, (nome, telas, res, desc, ativo, _) in enumerate(PLANOS, start=1)],
    )

    # ---------- plano_pais ----------
    precos = {}  # (cod_plano, cod_pais) -> (preco, moeda, disponivel)
    linhas = []
    for i, (nome, telas, res, desc, ativo, preco_brl) in enumerate(PLANOS, start=1):
        for p in paises:
            fator = FATOR_MOEDA[p["moeda"]]
            preco = round(preco_brl * fator * random.uniform(0.92, 1.08), 2)
            disponivel = not (nome == "Familia" and p["sigla"] in ("PY", "UY"))
            precos[(i, p["cod"])] = (preco, p["moeda"], disponivel)
            linhas.append((i, p["cod"], preco, p["moeda"], disponivel))
    guardar(
        "plano_pais",
        ["cod_plano", "cod_pais", "preco_mensal", "moeda",
         "indicador_disponibilidade"], linhas,
    )

    # ---------- endereco ----------
    enderecos = []  # (cod_endereco, cod_pais)
    linhas_end = []
    total_enderecos = QTD_ASSINANTES + QTD_FORNECEDORES
    for cod in range(1, total_enderecos + 1):
        p = random.choice(paises)
        enderecos.append((cod, p["cod"]))
        linhas_end.append([
            cod, p["cod"], random.choice(p["subdivisoes"]),
            fake.city()[:30], fake.bairro()[:40], fake.street_name()[:60],
            str(random.randint(1, 4999)),
            random.choice([None, "apto %d" % random.randint(11, 180),
                           "casa %d" % random.randint(1, 9), "bloco B"]),
            fake.postcode(),
        ])
    # guardado no fim: enderecos de titulares anonimizados sao sobrescritos

    # ---------- assinante + assinatura + historico + cobranca ----------
    TIPOS_DOC = {"BR": "CPF", "AR": "DNI", "CL": "RUT", "CO": "CC",
                 "MX": "CURP", "PE": "DNI", "UY": "CI", "PY": "CI"}
    assinantes = []
    linhas_assinante = []
    emails_usados = set()
    assinaturas = []
    linhas_ass = []
    linhas_hist = []
    linhas_cob = []
    cod_assinatura = 0
    limite_consulta = (DATA_REFERENCIA - timedelta(days=3)).date()

    for cod in range(1, QTD_ASSINANTES + 1):
        cod_endereco, cod_pais = enderecos[cod - 1]
        sigla = pais_por_cod[cod_pais]["sigla"]
        nome = fake.name()
        email = "%s%d@%s" % (
            nome.split()[0].lower().replace(".", ""), cod, fake.free_email_domain())
        while email in emails_usados:
            email = "u%d.%s" % (cod, email)
        emails_usados.add(email)
        nascimento = fake.date_of_birth(minimum_age=18, maximum_age=75)

        data_cadastro = data_hora_entre(datetime(2023, 1, 1),
                                        DATA_REFERENCIA - timedelta(days=45))

        # 10% trocaram de plano (so se houver tempo para duas vigencias)
        qtd = 1
        if (random.random() < 0.10
                and data_cadastro + timedelta(days=60)
                < DATA_REFERENCIA - timedelta(days=60)):
            qtd = 2

        # 4% dos assinantes pedem exclusao (LGPD); o pedido encerra a conta
        pediu_exclusao = random.random() < 0.04

        inicio_periodo = data_cadastro
        plano_anterior = None
        data_sol = None
        assinaturas_do_titular = []

        for n in range(qtd):
            ultima = (n == qtd - 1)
            # plano disponivel no pais; na troca, obrigatoriamente outro plano
            candidatos = [cp[0] for cp in precos
                          if cp[1] == cod_pais and precos[cp][2]
                          and cp[0] != plano_anterior]
            cod_plano = random.choice(candidatos)
            plano_anterior = cod_plano
            preco, moeda, _ = precos[(cod_plano, cod_pais)]

            cod_assinatura += 1
            data_inicio = inicio_periodo
            # cobranca acionada na data de aniversario da assinatura
            dia_venc = min(data_inicio.day, 28)

            # --- desfecho da assinatura ---
            data_cancel = None
            if not ultima:
                desfecho = "TROCA"
                data_cancel = data_hora_entre(
                    data_inicio + timedelta(days=60),
                    DATA_REFERENCIA - timedelta(days=60))
                inicio_periodo = data_cancel
            elif pediu_exclusao:
                desfecho = "EXCLUSAO"
                ini_sol = data_inicio + timedelta(days=30)
                if random.random() < 0.25:
                    # parte dos pedidos e recente e ainda esta no prazo
                    ini_sol = max(ini_sol,
                                  DATA_REFERENCIA - timedelta(days=14))
                data_sol = data_hora_entre(ini_sol, DATA_REFERENCIA)
                data_cancel = data_sol
            else:
                sorteio = random.random()
                if sorteio < 0.80:
                    desfecho = "ATIVA"
                elif sorteio < 0.90:
                    desfecho = "INADIMPLENTE"
                elif sorteio < 0.95:
                    desfecho = "SUSPENSA"
                else:
                    desfecho = "CANCELADA"
                if desfecho == "CANCELADA":
                    ini_c = data_inicio + timedelta(days=60)
                    if ini_c >= DATA_REFERENCIA:
                        desfecho = "ATIVA"
                    else:
                        data_cancel = data_hora_entre(ini_c, DATA_REFERENCIA)

            # --- vencimentos ja consultados no sistema financeiro ---
            limite = limite_consulta
            if data_cancel is not None:
                limite = min(limite, data_cancel.date())
            vencs = vencimentos(data_inicio.date(), dia_venc, limite)

            if desfecho == "SUSPENSA" and len(vencs) < 2:
                desfecho = "INADIMPLENTE"
            if desfecho == "INADIMPLENTE" and len(vencs) < 1:
                desfecho = "ATIVA"

            consultas = [
                datetime.combine(v, time(0, 0)) + timedelta(
                    days=2, hours=random.randint(0, 20),
                    minutes=random.randint(0, 59))
                for v in vencs
            ]
            situacoes = ["EM DIA"] * len(vencs)
            hist = [(data_inicio, cod_ativa, "Contratacao")]

            # atrasos passados que foram regularizados
            for i in range(len(vencs) - 2):
                if random.random() < 0.06:
                    situacoes[i] = "EM ATRASO"
                    hist.append((consultas[i], cod_inadimplente,
                                 "Pagamento nao identificado"))
                    hist.append((consultas[i] + timedelta(
                        days=random.randint(2, 15), hours=random.randint(0, 12)),
                        cod_ativa, "Pagamento regularizado"))

            # --- status final coerente com a cobranca ---
            data_fim = None
            if desfecho == "ATIVA":
                status_atual = cod_ativa
                fim_acesso = DATA_REFERENCIA
            elif desfecho == "INADIMPLENTE":
                status_atual = cod_inadimplente
                situacoes[-1] = "EM ATRASO"
                hist.append((consultas[-1], cod_inadimplente,
                             "Pagamento nao identificado"))
                fim_acesso = DATA_REFERENCIA  # acesso sob analise
            elif desfecho == "SUSPENSA":
                status_atual = cod_suspensa
                situacoes[-2] = "EM ATRASO"
                situacoes[-1] = "EM ATRASO"
                hist.append((consultas[-2], cod_inadimplente,
                             "Pagamento nao identificado"))
                hist.append((consultas[-1], cod_suspensa,
                             "Bloqueio por inadimplencia"))
                fim_acesso = consultas[-1]  # acesso bloqueado
            elif desfecho == "TROCA":
                status_atual = cod_cancelada
                data_fim = data_cancel  # migra na hora para o novo plano
                hist.append((data_cancel, cod_cancelada, "Troca de plano"))
                fim_acesso = data_cancel
            elif desfecho == "EXCLUSAO":
                status_atual = cod_cancelada
                data_fim = data_cancel  # pedido de exclusao encerra o acesso
                hist.append((data_cancel, cod_cancelada,
                             "Cancelamento por pedido de exclusao (LGPD)"))
                fim_acesso = data_cancel
            else:  # CANCELADA
                status_atual = cod_cancelada
                # acesso mantido ate o fim do periodo ja pago
                data_fim = datetime.combine(
                    proximo_vencimento(data_cancel, dia_venc), time(0, 0)
                ) - timedelta(seconds=1)
                hist.append((data_cancel, cod_cancelada,
                             "Cancelamento a pedido"))
                fim_acesso = min(data_fim, DATA_REFERENCIA)

            for momento, cod_st, motivo in hist:
                linhas_hist.append((cod_assinatura, momento, cod_st, motivo))
            for v, comp_consulta, sit in zip(vencs, consultas, situacoes):
                linhas_cob.append((
                    cod_assinatura, "%04d-%02d" % (v.year, v.month), preco,
                    moeda, v, sit, comp_consulta,
                ))

            reg = {
                "cod": cod_assinatura, "cod_assinante": cod,
                "cod_pais": cod_pais, "inicio": data_inicio,
                "fim": fim_acesso, "status": status_atual,
                "telas": PLANOS[cod_plano - 1][1],
                "anon_titular": None,
            }
            assinaturas.append(reg)
            assinaturas_do_titular.append(reg)
            linhas_ass.append((
                cod_assinatura, cod, cod_plano, cod_pais,
                data_inicio, dia_venc, preco, moeda, status_atual,
                data_cancel, data_fim,
            ))

        # --- situacao LGPD do titular ---
        situacao = "ATIVO"
        data_anon = None
        if pediu_exclusao:
            situacao = "EXCLUSAO_SOLICITADA"
            prazo = data_sol + timedelta(
                days=random.randint(1, PRAZO_ANONIMIZACAO_DIAS),
                hours=random.randint(0, 12))
            prazo = min(prazo, data_sol
                        + timedelta(days=PRAZO_ANONIMIZACAO_DIAS))
            if prazo <= DATA_REFERENCIA:
                data_anon = prazo
                situacao = "ANONIMIZADO"
            for reg in assinaturas_do_titular:
                reg["anon_titular"] = data_anon

        linha = [
            cod, nome[:128], TIPOS_DOC[sigla],
            fake.sha256()[:64] + fake.sha256()[:64],  # documento_hash (128)
            email[:128],
            fake.sha256()[:64] + fake.sha256()[:64],  # senha_hash (128)
            fake.md5()[:32],                          # salt (32)
            fake.msisdn()[:20], nascimento,
            data_cadastro, cod_endereco, situacao, data_sol, data_anon,
        ]
        if data_anon is not None:
            # dados pessoais sobrescritos; hashes novos preservam a unicidade
            linha[1] = "Titular anonimizado"
            linha[3] = fake.sha256()[:64] + fake.sha256()[:64]
            linha[4] = "anon_%d@artflix.invalid" % cod
            linha[5] = fake.sha256()[:64] + fake.sha256()[:64]
            linha[6] = fake.md5()[:32]
            linha[7] = TEXTO_ANONIMO
            linha[8] = date(nascimento.year, 1, 1)  # so o ano
            end = linhas_end[cod_endereco - 1]
            end[3] = TEXTO_ANONIMO   # cidade
            end[4] = TEXTO_ANONIMO   # bairro
            end[5] = TEXTO_ANONIMO   # logradouro
            end[6] = "S/N"           # numero
            end[7] = None            # complemento
            end[8] = TEXTO_ANONIMO   # codigo_postal
        linhas_assinante.append(tuple(linha))
        assinantes.append({"cod": cod, "cod_pais": cod_pais,
                           "nascimento": nascimento, "anon": data_anon})

    guardar(
        "endereco",
        ["cod_endereco", "cod_pais", "subdivisao", "cidade", "bairro",
         "logradouro", "numero", "complemento", "codigo_postal"],
        [tuple(e) for e in linhas_end],
    )
    guardar(
        "assinante",
        ["cod_assinante", "nome_completo", "tipo_documento", "documento_hash",
         "email", "senha_hash", "salt", "telefone", "data_nascimento",
         "data_cadastro", "cod_endereco", "situacao_cadastro",
         "data_solicitacao_exclusao", "data_anonimizacao"], linhas_assinante,
    )
    guardar(
        "assinatura",
        ["cod_assinatura", "cod_assinante", "cod_plano", "cod_pais",
         "data_inicio", "dia_vencimento", "valor_contratado", "moeda",
         "cod_status", "data_cancelamento", "data_fim_acesso"], linhas_ass,
    )
    guardar(
        "historico",
        ["cod_assinatura", "data_hora_status", "cod_status", "motivo"],
        linhas_hist,
    )
    guardar(
        "cobranca",
        ["cod_assinatura", "competencia", "valor_cobrado", "moeda",
         "data_vencimento", "situacao_pagamento", "data_consulta"], linhas_cob,
    )

    # ---------- perfil ----------
    NOMES_PERFIL = ["Infantil", "Visitante", "Sala", "Quarto",
                    "Familia", "Trabalho", "Fim de semana"]
    perfis = []
    linhas = []
    cod_perfil = 0
    for ass in assinaturas:
        titular = assinantes[ass["cod_assinante"] - 1]
        qtd_perfis = min(random.randint(1, 5), ass["telas"] + 1, 5)
        # o perfil Principal e do titular e nasce junto com a assinatura
        nomes = ["Principal"] + random.sample(NOMES_PERFIL, qtd_perfis - 1)
        for nome_p in nomes:
            cod_perfil += 1
            if nome_p == "Principal":
                infantil = False
                nascimento = titular["nascimento"]
                cod_class = 6
                criacao = ass["inicio"]
            else:
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
            if ass["anon_titular"] is not None:
                nascimento = date(nascimento.year, 1, 1)  # so o ano
            perfis.append({
                "cod": cod_perfil, "cod_pais": ass["cod_pais"],
                "limite": CLASSIFICACOES[cod_class - 1][1],
                "criacao": criacao, "fim": ass["fim"],
                "anon_titular": ass["anon_titular"],
            })
            linhas.append((
                cod_perfil, ass["cod"], nome_p, nascimento, cod_class,
                "avatar_%02d.png" % random.randint(1, 20), infantil, criacao,
            ))
    guardar(
        "perfil",
        ["cod_perfil", "cod_assinatura", "nome_perfil", "data_nascimento",
         "cod_classificacao", "avatar", "indicador_infantil", "data_criacao"],
        linhas,
    )

    # ---------- dispositivo ----------
    dispositivos = []
    linhas = []
    for cod in range(1, QTD_DISPOSITIVOS + 1):
        tipo = random.choice(list(DISPOSITIVOS))
        so, fabricantes = random.choice(DISPOSITIVOS[tipo])
        dispositivos.append({"cod": cod, "tipo": tipo})
        linhas.append((
            cod, fake.uuid4(), tipo, so,
            "%s %d" % (random.choice(["Serie", "Modelo", "Linha"]),
                       random.randint(1, 40)),
            random.choice(fabricantes),
        ))
    guardar(
        "dispositivo",
        ["cod_dispositivo", "identificador_dispositivo", "tipo_dispositivo",
         "sistema_operacional", "modelo", "fabricante"], linhas,
    )

    # ---------- titulo ----------
    titulos = []
    linhas = []
    nomes_usados = set()
    for cod in range(1, QTD_TITULOS + 1):
        tipo = random.choices(TIPOS_TITULO, weights=PESOS_TIPO_TITULO)[0]
        nome = "%s %s" % (random.choice(PALAVRAS_TITULO_A),
                          random.choice(PALAVRAS_TITULO_B))
        ano = random.randint(1995, 2026)
        while (nome, ano) in nomes_usados:
            nome = "%s %s II" % (random.choice(PALAVRAS_TITULO_A),
                                 random.choice(PALAVRAS_TITULO_B))
            ano = random.randint(1995, 2026)
        nomes_usados.add((nome, ano))

        if tipo == "DOCUMENTARIO":
            duracao = random.randint(2700, 6000)
        else:
            duracao = random.randint(4500, 10800)

        cod_class = random.choices([1, 2, 3, 4, 5, 6],
                                   weights=[20, 15, 20, 15, 15, 15])[0]
        pais_origem = random.choice(paises)
        titulos.append({"cod": cod, "duracao": duracao, "classe": cod_class,
                        "idade": CLASSIFICACOES[cod_class - 1][1], "ano": ano})
        linhas.append((
            cod, nome, tipo, ano, duracao,
            fake.sentence(nb_words=18)[:400],
            pais_origem["idioma"],  # idioma original coerente com a origem
            pais_origem["cod"], cod_class,
        ))
    guardar(
        "titulo",
        ["cod_titulo", "nome_titulo", "tipo_titulo", "ano_lancamento",
         "duracao_segundos", "sinopse", "idioma_original", "cod_pais_origem",
         "cod_classificacao"], linhas,
    )

    # ---------- titulo_genero (N:N) ----------
    linhas = []
    for t in titulos:
        for cod_gen in random.sample(range(1, len(GENEROS) + 1),
                                     random.randint(1, 3)):
            linhas.append((t["cod"], cod_gen))
    guardar("titulo_genero", ["cod_titulo", "cod_genero"], linhas)

    # ---------- fornecedor ----------
    linhas = []
    for cod in range(1, QTD_FORNECEDORES + 1):
        cod_endereco = QTD_ASSINANTES + cod
        razao = fake.company()
        linhas.append((
            cod, razao[:80], razao.split()[0][:60], fake.cnpj(),
            "contato@%s" % fake.domain_name(), fake.msisdn()[:20], cod_endereco,
        ))
    guardar(
        "fornecedor",
        ["cod_fornecedor", "razao_social", "nome_fantasia", "documento_fiscal",
         "email_contato", "telefone_contato", "cod_endereco"], linhas,
    )

    # ---------- contrato (datas) ----------
    contratos = []
    for cod in range(1, QTD_CONTRATOS + 1):
        cod_forn = random.randint(1, QTD_FORNECEDORES)
        assinatura_ct = fake.date_between(date(2022, 1, 1), date(2025, 6, 30))
        inicio = assinatura_ct + timedelta(days=random.randint(5, 60))
        fim = inicio + timedelta(days=random.randint(365, 1460))
        contratos.append({
            "cod": cod, "fornecedor": cod_forn, "assinatura": assinatura_ct,
            "inicio": inicio, "fim": fim,
            "moeda": random.choice(MOEDAS_LICENCIAMENTO), "soma_licencas": 0.0,
        })

    # ---------- janela ----------
    janelas = []
    linhas = []
    chaves = set()
    ocupacao = {}  # (titulo, pais) -> [(inicio, fim, exclusiva)]
    cod_janela = 0
    tentativas = 0
    while len(janelas) < QTD_JANELAS and tentativas < QTD_JANELAS * 40:
        tentativas += 1
        ct = random.choice(contratos)
        t = random.choice(titulos)
        p = random.choice(paises)
        inicio = ct["inicio"] + timedelta(days=random.randint(0, 200))
        if inicio >= ct["fim"]:
            continue
        # nao se licencia titulo antes do seu ano de lancamento
        if inicio < date(t["ano"], 1, 1):
            continue
        chave = (ct["cod"], t["cod"], p["cod"], inicio)
        if chave in chaves:
            continue
        fim = min(inicio + timedelta(days=random.randint(180, 1095)), ct["fim"])
        if fim <= inicio:
            continue
        # exclusividade: janela exclusiva nao se sobrepoe a nenhuma outra
        exclusiva = random.random() < 0.2
        conflito = False
        for (i2, f2, ex2) in ocupacao.get((t["cod"], p["cod"]), []):
            if inicio < f2 and i2 < fim and (exclusiva or ex2):
                conflito = True
                break
        if conflito:
            continue
        chaves.add(chave)
        ocupacao.setdefault((t["cod"], p["cod"]), []).append(
            (inicio, fim, exclusiva))
        cod_janela += 1
        # licenca na moeda do contrato
        valor = random.uniform(5_000, 300_000) * (1.5 if exclusiva else 1.0)
        if ct["moeda"] == "USD":
            valor /= TAXA_USD["BRL"]
        valor = round(valor, 2)
        ct["soma_licencas"] += valor
        janelas.append({
            "cod": cod_janela, "titulo": t["cod"], "pais": p["cod"],
            "inicio": inicio, "fim": fim, "idade": t["idade"],
            "duracao": t["duracao"],
        })
        linhas.append((
            cod_janela, ct["cod"], t["cod"], p["cod"], inicio, fim,
            exclusiva, valor, ct["moeda"],
        ))
    linhas_janela = linhas

    # ---------- contrato (valores) ----------
    # o valor total cobre a soma das licencas das janelas do contrato
    linhas = []
    for ct in contratos:
        if ct["soma_licencas"] > 0:
            total = ct["soma_licencas"] * random.uniform(1.05, 1.25)
        else:
            total = random.uniform(150_000, 1_000_000)
            if ct["moeda"] == "USD":
                total /= TAXA_USD["BRL"]
        situacao = "VIGENTE" if ct["fim"] >= DATA_REFERENCIA.date() else "ENCERRADO"
        linhas.append((
            ct["cod"], ct["fornecedor"],
            "CT-%04d/%d" % (ct["cod"], ct["assinatura"].year),
            ct["assinatura"], ct["inicio"], ct["fim"],
            round(total, 2), ct["moeda"], situacao,
        ))
    guardar(
        "contrato",
        ["cod_contrato", "cod_fornecedor", "numero_contrato", "data_assinatura",
         "data_inicio_vigencia", "data_fim_vigencia", "valor_total", "moeda",
         "situacao_contrato"], linhas,
    )
    guardar(
        "janela",
        ["cod_janela", "cod_contrato", "cod_titulo", "cod_pais", "data_inicio",
         "data_fim", "indicador_exclusividade", "valor_licenca", "moeda"],
        linhas_janela,
    )

    # indexa janelas e perfis por pais
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
        # login so enquanto o acesso esta liberado
        momento = data_hora_entre(pf["criacao"], max(pf["fim"], pf["criacao"]))
        disp = random.choice(dispositivos)
        # GPS so em dispositivo que tem GPS integrado
        tem_gps = disp["tipo"] in TIPOS_COM_GPS and random.random() < 0.7
        lat = lon = None
        if tem_gps:
            clat, clon, raio = pais_por_cod[pf["cod_pais"]]["gps"]
            lat = round(clat + random.uniform(-raio, raio), 6)
            lon = round(clon + random.uniform(-raio, raio), 6)
        ip = fake.ipv4_public()
        anon = anonimizacao_consumo(momento, pf["anon_titular"])
        if anon is not None:
            ip = mascarar_ip(ip)
            lat = lon = None
        linhas.append((cod, pf["cod"], disp["cod"], momento, ip,
                       lat, lon, tem_gps, anon))
    guardar(
        "login",
        ["cod_login", "cod_perfil", "cod_dispositivo", "data_hora_login",
         "endereco_ip", "latitude", "longitude", "indicador_gps",
         "data_anonimizacao"], linhas,
    )

    # ---------- pesquisa ----------
    linhas = []
    for cod in range(1, QTD_PESQUISAS + 1):
        pf = random.choice(perfis)
        momento = data_hora_entre(pf["criacao"], max(pf["fim"], pf["criacao"]))
        anon = anonimizacao_consumo(momento, pf["anon_titular"])
        linhas.append((cod, pf["cod"], random.choice(TERMOS_PESQUISA), momento,
                       random.randint(0, 60), anon))
    guardar(
        "pesquisa",
        ["cod_pesquisa", "cod_perfil", "termo_pesquisado", "data_hora_pesquisa",
         "qtd_resultados", "data_anonimizacao"], linhas,
    )

    # ---------- sessoes ----------
    linhas = []
    primeira_sessao = {}  # (perfil, titulo) -> (fim da 1a sessao, perfil)
    cod_sessao = 0
    tentativas = 0
    limite = QTD_SESSOES * 40
    while cod_sessao < QTD_SESSOES and tentativas < limite:
        tentativas += 1
        cod_pais = random.choice(paises_com_dados)
        pf = random.choice(perfis_por_pais[cod_pais])
        j = random.choice(janelas_por_pais[cod_pais])

        # regra: classificacao do titulo <= limite do perfil
        if j["idade"] > pf["limite"]:
            continue

        # regra: sessao dentro da janela vigente e do acesso liberado
        ini = max(datetime.combine(j["inicio"], time(0, 0)), pf["criacao"])
        fim = min(datetime.combine(j["fim"], time(0, 0)),
                  pf["fim"], DATA_REFERENCIA)
        if fim <= ini:
            continue

        momento = data_hora_entre(ini, fim)
        # regra: sessao so conta acima de 60 segundos
        assistido = random.randint(61, j["duracao"])
        ip = fake.ipv4_public()
        anon = anonimizacao_consumo(momento, pf["anon_titular"])
        if anon is not None:
            ip = mascarar_ip(ip)

        cod_sessao += 1
        linhas.append((cod_sessao, pf["cod"], j["titulo"],
                       random.choice(dispositivos)["cod"], cod_pais, j["cod"],
                       momento, assistido, ip, anon))
        fim_sessao = momento + timedelta(seconds=assistido)
        par = (pf["cod"], j["titulo"])
        if par not in primeira_sessao or fim_sessao < primeira_sessao[par][0]:
            primeira_sessao[par] = (fim_sessao, pf)
    guardar(
        "sessoes",
        ["cod_sessao", "cod_perfil", "cod_titulo", "cod_dispositivo",
         "cod_pais", "cod_janela", "data_hora_inicio", "segundos_assistidos",
         "endereco_ip", "data_anonimizacao"], linhas,
    )
    print("  sessoes geradas: %d" % cod_sessao)

    # ---------- avaliacao ----------
    # o perfil so avalia titulo que ja assistiu, depois da primeira sessao
    linhas = []
    pares = sorted(primeira_sessao)
    for par in random.sample(pares, min(QTD_AVALIACOES, len(pares))):
        fim_sessao, pf = primeira_sessao[par]
        teto = min(pf["fim"], DATA_REFERENCIA)
        if fim_sessao > teto:
            fim_sessao = teto
        momento = data_hora_entre(fim_sessao,
                                  min(fim_sessao + timedelta(days=30), teto))
        nota = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 25, 35, 25])[0]
        linhas.append((par[0], par[1], nota, momento))
    linhas.sort()
    guardar(
        "avaliacao",
        ["cod_perfil", "cod_titulo", "nota", "data_hora_avaliacao"], linhas,
    )
    print("  avaliacoes geradas: %d" % len(linhas))

    # ---------- escrita ----------
    # se uma tabela nova entrou na carga e nao foi incluida em TABELAS, ela
    # ficaria de fora da limpeza e so daria erro de duplicata no Workbench
    faltando = set(SAIDA) - set(TABELAS)
    if faltando:
        raise SystemExit("tabelas fora da limpeza: %s" % sorted(faltando))

    arq = open(ARQUIVO_SAIDA, "w", encoding="utf-8")
    arq.write("-- Carga de dados de exemplo do ARTFLIX\n")
    arq.write("-- Gerado por gerar_dados_artflix.py (semente = %d)\n" % SEED)
    arq.write("-- Este arquivo e derivado: nao precisa ir para o GitHub.\n\n")
    arq.write("SET NAMES utf8mb4;\n")
    arq.write("USE `ppgcd_artflix_db`;\n")
    arq.write("SET FOREIGN_KEY_CHECKS = 0;\n")
    arq.write("SET UNIQUE_CHECKS = 0;\n")
    arq.write("SET AUTOCOMMIT = 0;\n")

    # ---------- limpeza ----------
    # torna a carga reexecutavel sobre um banco ja povoado.
    # depende do FOREIGN_KEY_CHECKS = 0 escrito acima: sem isso o InnoDB
    # recusa TRUNCATE em tabela que e pai de alguma FK.
    # atencao: TRUNCATE e DDL, faz commit implicito e nao volta com ROLLBACK.
    arq.write("\n-- limpeza: torna a carga reexecutavel sobre um banco ja povoado\n")
    for tabela in reversed(TABELAS):
        arq.write("TRUNCATE TABLE `%s`;\n" % tabela)
    arq.write("\n")

    for tabela in TABELAS:
        if tabela in SAIDA:
            colunas, linhas = SAIDA[tabela]
            escrever_insert(arq, tabela, colunas, linhas)

    arq.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
    arq.write("SET UNIQUE_CHECKS = 1;\n")
    arq.write("COMMIT;\n")
    arq.close()

    import os
    tamanho = os.path.getsize(ARQUIVO_SAIDA) / (1024 * 1024)
    print("Pronto: %s (%.1f MB)" % (ARQUIVO_SAIDA, tamanho))


if __name__ == "__main__":
    main()
