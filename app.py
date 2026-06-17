import pandas as pd
import streamlit as st

from src.nfe_parser import parsear_varios_xmls
from src.simulador_desmembramento import simular_desmembramento

st.set_page_config(
    page_title="Calculadora Redução",
    page_icon="🧮",
    layout="wide",
)


USUARIOS = {
    "admin": "112211bb",
    "guilherme": "112211bb",
}


def tela_login():
    """
    Tela simples de login com usuário e senha.
    Mantém o usuário logado usando st.session_state.
    """
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None

    if st.session_state.autenticado:
        with st.sidebar:
            st.success(f"Logado como: {st.session_state.usuario_logado}")

            if st.button("Sair"):
                st.session_state.autenticado = False
                st.session_state.usuario_logado = None
                st.rerun()

        return True

    st.title("Acesso ao sistema")
    st.caption("Informe usuário e senha para acessar a calculadora.")

    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        entrar = st.form_submit_button("Entrar")

    if entrar:
        usuario = usuario.strip()

        if usuario in USUARIOS and senha == USUARIOS[usuario]:
            st.session_state.autenticado = True
            st.session_state.usuario_logado = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    return False


if not tela_login():
    st.stop()


def valor_float(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao

        valor_texto = str(valor).replace(",", ".").strip()

        if valor_texto == "" or valor_texto.lower() == "nan":
            return padrao

        return float(valor_texto)
    except Exception:
        return padrao


def montar_descricao_produto(linha):
    nf = linha.get("Número NF", "")
    item = linha.get("Número item", "")
    codigo = linha.get("Código produto XML", "")
    descricao = linha.get("Descrição produto", "")
    qtd = linha.get("qTrib", "")

    return f"NF {nf} | Item {item} | Cód. {codigo} | Qtd: {qtd} | {descricao}"


def config_colunas_resultado_xml():
    return {
        "qTrib": st.column_config.NumberColumn("qTrib", format="%.4f"),
        "vUnTrib": st.column_config.NumberColumn("vUnTrib", format="%.6f"),
        "Valor produto": st.column_config.NumberColumn("Valor produto", format="%.2f"),
        "vOutro": st.column_config.NumberColumn("vOutro", format="%.2f"),
        "vBC": st.column_config.NumberColumn("vBC", format="%.2f"),
        "pICMS": st.column_config.NumberColumn("pICMS", format="%.2f"),
        "vICMS": st.column_config.NumberColumn("vICMS", format="%.2f"),
        "Base PIS XML": st.column_config.NumberColumn("Base PIS XML", format="%.2f"),
        "Alíquota PIS XML": st.column_config.NumberColumn(
            "Alíquota PIS XML",
            format="%.2f",
        ),
        "Valor PIS XML": st.column_config.NumberColumn("Valor PIS XML", format="%.2f"),
        "Base COFINS XML": st.column_config.NumberColumn(
            "Base COFINS XML",
            format="%.2f",
        ),
        "Alíquota COFINS XML": st.column_config.NumberColumn(
            "Alíquota COFINS XML",
            format="%.2f",
        ),
        "Valor COFINS XML": st.column_config.NumberColumn(
            "Valor COFINS XML",
            format="%.2f",
        ),
        "Base PIS/COFINS calculada": st.column_config.NumberColumn(
            "Base PIS/COFINS calculada",
            format="%.2f",
        ),
        "pRedBC XML": st.column_config.NumberColumn("pRedBC XML", format="%.4f"),
        "pRedBC calculado": st.column_config.NumberColumn(
            "pRedBC calculado",
            format="%.4f",
        ),
    }


def config_colunas_simulador():
    return {
        "Quantidade": st.column_config.NumberColumn("Quantidade", format="%.4f"),
        "vUnTrib": st.column_config.NumberColumn("vUnTrib", format="%.6f"),
        "Valor produto": st.column_config.NumberColumn("Valor produto", format="%.2f"),
        "vOutro": st.column_config.NumberColumn("vOutro", format="%.2f"),
        "Valor referência": st.column_config.NumberColumn(
            "Valor referência",
            format="%.2f",
        ),
        "vBC": st.column_config.NumberColumn("vBC", format="%.2f"),
        "pICMS": st.column_config.NumberColumn("pICMS", format="%.2f"),
        "vICMS": st.column_config.NumberColumn("vICMS", format="%.2f"),
        "Base PIS/COFINS calculada": st.column_config.NumberColumn(
            "Base PIS/COFINS calculada",
            format="%.2f",
        ),
        "Base PIS XML proporcional": st.column_config.NumberColumn(
            "Base PIS XML proporcional",
            format="%.2f",
        ),
        "Alíquota PIS XML": st.column_config.NumberColumn(
            "Alíquota PIS XML",
            format="%.2f",
        ),
        "Valor PIS XML proporcional": st.column_config.NumberColumn(
            "Valor PIS XML proporcional",
            format="%.2f",
        ),
        "Base COFINS XML proporcional": st.column_config.NumberColumn(
            "Base COFINS XML proporcional",
            format="%.2f",
        ),
        "Alíquota COFINS XML": st.column_config.NumberColumn(
            "Alíquota COFINS XML",
            format="%.2f",
        ),
        "Valor COFINS XML proporcional": st.column_config.NumberColumn(
            "Valor COFINS XML proporcional",
            format="%.2f",
        ),
        "pRedBC XML": st.column_config.NumberColumn("pRedBC XML", format="%.4f"),
        "pRedBC calculado": st.column_config.NumberColumn(
            "pRedBC calculado",
            format="%.4f",
        ),
    }


st.title("Calculadora de redução de base ICMS em XML de NF-e")
st.caption(
    "Upload de XML, leitura dos itens, cálculo do pRedBC e simulação de desmembramento proporcional."
)

with st.expander("Fórmula utilizada", expanded=True):
    st.code(
        "pRedBC calculado = 100 - ((vBC / ((qTrib * vUnTrib) + vOutro)) * 100)",
        language="text",
    )
    st.write("Quando `vOutro` não existir no XML, ele é considerado como `0`.")
    st.write("Base PIS/COFINS calculada = Valor produto - vICMS.")


arquivos_xml = st.file_uploader(
    "Selecione um ou vários XMLs de NF-e",
    type=["xml"],
    accept_multiple_files=True,
)


if not arquivos_xml:
    st.info("Envie um ou mais arquivos XML de NF-e para iniciar a análise.")
    st.stop()


try:
    linhas = parsear_varios_xmls(arquivos_xml)
except Exception as erro:
    st.error(f"Erro ao processar XML: {erro}")
    st.stop()


if not linhas:
    st.warning("Nenhum item de NF-e foi encontrado nos XMLs enviados.")
    st.stop()


df = pd.DataFrame(linhas)


col1, col2, col3, col4 = st.columns(4)

col1.metric("XMLs enviados", len(arquivos_xml))
col2.metric("Itens lidos", len(df))
col3.metric("Notas", df["Chave de acesso"].nunique())
col4.metric("Itens com pRedBC XML", int(df["pRedBC XML"].notna().sum()))


aba_resultado, aba_simulador = st.tabs(
    [
        "Resultado XML",
        "Simulador de desmembramento",
    ]
)


with aba_resultado:
    st.subheader("Itens extraídos do XML")
    st.caption(
        "Clique na coluna lateral da tabela para selecionar um item. "
        "A linha selecionada fica marcada por inteiro para facilitar a navegação."
    )

    evento_tabela_xml = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=config_colunas_resultado_xml(),
        selection_mode="single-row",
        on_select="rerun",
        key="tabela_itens_xml",
    )

    linhas_selecionadas = evento_tabela_xml.selection.rows

    if linhas_selecionadas:
        posicao_linha_selecionada = linhas_selecionadas[0]
        st.session_state["linha_xml_selecionada"] = posicao_linha_selecionada

        item_marcado = df.iloc[posicao_linha_selecionada]
        st.info(
            "Item selecionado: "
            f"NF {item_marcado.get('Número NF', '')} | "
            f"Item {item_marcado.get('Número item', '')} | "
            f"Código {item_marcado.get('Código produto XML', '')} | "
            f"{item_marcado.get('Descrição produto', '')}"
        )


with aba_simulador:
    st.subheader("Simulador de desmembramento de item")

    st.write(
        "Selecione um item da NF-e e informe a quantidade que será desmembrada. "
        "O sistema calcula proporcionalmente os valores de ICMS, PIS e COFINS."
    )

    colunas_obrigatorias = [
        "Número NF",
        "Número item",
        "Código produto XML",
        "Descrição produto",
        "qTrib",
        "vUnTrib",
        "Valor produto",
        "vBC",
        "pICMS",
        "vICMS",
        "Base PIS/COFINS calculada",
        "Base PIS XML",
        "Alíquota PIS XML",
        "Valor PIS XML",
        "Base COFINS XML",
        "Alíquota COFINS XML",
        "Valor COFINS XML",
    ]

    colunas_faltando = [
        coluna for coluna in colunas_obrigatorias if coluna not in df.columns
    ]

    if colunas_faltando:
        st.error(
            "Não foi possível montar o simulador. "
            f"Colunas faltando no resultado do XML: {', '.join(colunas_faltando)}"
        )
        st.stop()

    df_simulador = df.copy()

    df_simulador["Produto para seleção"] = df_simulador.apply(
        montar_descricao_produto,
        axis=1,
    )

    opcoes_simulador = df_simulador.index.tolist()
    indice_padrao_simulador = 0

    if "linha_xml_selecionada" in st.session_state:
        posicao_salva = int(st.session_state["linha_xml_selecionada"])

        if 0 <= posicao_salva < len(opcoes_simulador):
            indice_padrao_simulador = posicao_salva

    indice_selecionado = st.selectbox(
        "Selecione o produto da NF-e",
        options=opcoes_simulador,
        index=indice_padrao_simulador,
        format_func=lambda indice: df_simulador.loc[indice, "Produto para seleção"],
    )

    item_original = df_simulador.loc[indice_selecionado].to_dict()

    quantidade_original = valor_float(item_original.get("qTrib"))

    if quantidade_original <= 0:
        st.error("A quantidade original do item é inválida para simulação.")
        st.stop()

    st.markdown("### Dados originais do item")

    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)

    col_a.metric("Quantidade original", f"{quantidade_original:.4f}")
    col_b.metric("vUnTrib", f"{valor_float(item_original.get('vUnTrib')):.6f}")
    col_c.metric(
        "Valor produto", f"{valor_float(item_original.get('Valor produto')):.2f}"
    )
    col_d.metric("vBC ICMS", f"{valor_float(item_original.get('vBC')):.2f}")
    col_e.metric("vICMS", f"{valor_float(item_original.get('vICMS')):.2f}")
    col_f.metric(
        "Base PIS/COFINS",
        f"{valor_float(item_original.get('Base PIS/COFINS calculada')):.2f}",
    )

    col_pis1, col_pis2, col_pis3, col_cof1, col_cof2, col_cof3 = st.columns(6)

    col_pis1.metric(
        "Base PIS XML", f"{valor_float(item_original.get('Base PIS XML')):.2f}"
    )
    col_pis2.metric(
        "Alíquota PIS XML",
        f"{valor_float(item_original.get('Alíquota PIS XML')):.2f}%",
    )
    col_pis3.metric(
        "Valor PIS XML", f"{valor_float(item_original.get('Valor PIS XML')):.2f}"
    )

    col_cof1.metric(
        "Base COFINS XML",
        f"{valor_float(item_original.get('Base COFINS XML')):.2f}",
    )
    col_cof2.metric(
        "Alíquota COFINS XML",
        f"{valor_float(item_original.get('Alíquota COFINS XML')):.2f}%",
    )
    col_cof3.metric(
        "Valor COFINS XML",
        f"{valor_float(item_original.get('Valor COFINS XML')):.2f}",
    )

    with st.expander("Ver dados completos do item selecionado", expanded=False):
        st.dataframe(
            pd.DataFrame([item_original]),
            use_container_width=True,
            hide_index=True,
            column_config=config_colunas_resultado_xml(),
        )

    quantidade_desmembrada = st.number_input(
        "Quantidade a desmembrar",
        min_value=0.0001,
        max_value=float(quantidade_original),
        value=1.0000 if quantidade_original >= 1 else float(quantidade_original),
        step=1.0000,
        format="%.4f",
    )

    quantidade_restante = quantidade_original - quantidade_desmembrada

    col_qtd1, col_qtd2, col_qtd3 = st.columns(3)

    col_qtd1.metric("Quantidade original", f"{quantidade_original:.4f}")
    col_qtd2.metric("Quantidade desmembrada", f"{quantidade_desmembrada:.4f}")
    col_qtd3.metric("Quantidade restante", f"{quantidade_restante:.4f}")

    if st.button("Simular desmembramento", type="primary"):
        try:
            resultado_simulacao = simular_desmembramento(
                item_original=item_original,
                quantidade_desmembrada=quantidade_desmembrada,
            )

            df_resultado_simulacao = pd.DataFrame(resultado_simulacao)

            st.markdown("### Resultado da simulação")

            st.dataframe(
                df_resultado_simulacao,
                use_container_width=True,
                hide_index=True,
                column_config=config_colunas_simulador(),
            )

        except ValueError as erro:
            st.error(str(erro))
        except Exception as erro:
            st.error(f"Erro ao simular desmembramento: {erro}")
