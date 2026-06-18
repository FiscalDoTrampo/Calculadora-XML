from __future__ import annotations

import xml.etree.ElementTree as ET
from decimal import Decimal
from typing import Iterable, Optional

from .calculos import (
    CRITERIO_REFERENCIA_PADRAO,
    arredondar_2,
    calcular_predbc,
    calcular_valor_referencia_icms,
    descricao_criterio_referencia_icms,
    para_decimal,
)


def nome_local(tag: str) -> str:
    """Remove namespace da tag XML, mantendo apenas o nome local."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def primeiro_filho(elemento: Optional[ET.Element], nome: str) -> Optional[ET.Element]:
    """Localiza o primeiro filho direto pelo nome local, ignorando namespace."""
    if elemento is None:
        return None

    for filho in list(elemento):
        if nome_local(filho.tag) == nome:
            return filho
    return None


def todos_filhos(elemento: Optional[ET.Element], nome: str) -> list[ET.Element]:
    """Localiza todos os filhos diretos pelo nome local, ignorando namespace."""
    if elemento is None:
        return []
    return [filho for filho in list(elemento) if nome_local(filho.tag) == nome]


def texto(elemento: Optional[ET.Element], nome: str, padrao: str = "") -> str:
    """Extrai texto de um filho direto pelo nome local."""
    filho = primeiro_filho(elemento, nome)
    if filho is None or filho.text is None:
        return padrao
    return filho.text.strip()


def decimal_2_para_float(valor: object) -> Optional[float]:
    """Converte para float arredondado em 2 casas para exibição no Pandas/Streamlit."""
    valor_decimal = arredondar_2(para_decimal(valor))
    if valor_decimal is None:
        return None
    return float(valor_decimal)


def decimal_4_para_float(valor: object) -> Optional[float]:
    """Converte para float arredondado em 4 casas para quantidade/percentuais."""
    valor_decimal = para_decimal(valor)
    if valor_decimal is None:
        return None
    return float(valor_decimal.quantize(Decimal("0.0001")))


def decimal_para_float(valor: Optional[Decimal], casas: int = 2) -> Optional[float]:
    """Converte Decimal para float mantendo None quando não houver valor."""
    if valor is None:
        return None

    if casas == 4:
        return float(valor.quantize(Decimal("0.0001")))

    return float(arredondar_2(valor))


def localizar_inf_nfe(raiz: ET.Element) -> Optional[ET.Element]:
    """Localiza a tag infNFe em XML com ou sem nfeProc."""
    if nome_local(raiz.tag) == "infNFe":
        return raiz

    for elemento in raiz.iter():
        if nome_local(elemento.tag) == "infNFe":
            return elemento
    return None


def extrair_chave(inf_nfe: Optional[ET.Element], raiz: ET.Element) -> str:
    """Extrai a chave de acesso pelo Id da infNFe ou pela tag chNFe."""
    if inf_nfe is not None:
        chave = inf_nfe.attrib.get("Id", "").strip()
        if chave.startswith("NFe"):
            return chave[3:]
        if chave:
            return chave

    for elemento in raiz.iter():
        if nome_local(elemento.tag) == "chNFe" and elemento.text:
            return elemento.text.strip()

    return ""


def localizar_grupo_icms(imposto: Optional[ET.Element]) -> Optional[ET.Element]:
    """Retorna o grupo ICMS do item, por exemplo ICMS20, ICMS70 ou ICMSSN201."""
    icms = primeiro_filho(imposto, "ICMS")
    if icms is None:
        return None

    for grupo in list(icms):
        if nome_local(grupo.tag).startswith("ICMS"):
            return grupo
    return None


def localizar_grupo_tributo(
    imposto: Optional[ET.Element], nome_tributo: str
) -> Optional[ET.Element]:
    """
    Localiza o grupo interno de PIS ou COFINS.

    Exemplos:
    PIS > PISAliq
    PIS > PISNT
    PIS > PISOutr
    COFINS > COFINSAliq
    COFINS > COFINSNT
    COFINS > COFINSOutr
    """
    tributo = primeiro_filho(imposto, nome_tributo)

    if tributo is None:
        return None

    for grupo in list(tributo):
        return grupo

    return tributo


def localizar_grupo_pis(imposto: Optional[ET.Element]) -> Optional[ET.Element]:
    """Localiza PIS ou PISST no grupo imposto."""
    grupo = localizar_grupo_tributo(imposto, "PIS")
    if grupo is not None:
        return grupo
    return primeiro_filho(imposto, "PISST")


def localizar_grupo_cofins(imposto: Optional[ET.Element]) -> Optional[ET.Element]:
    """Localiza COFINS ou COFINSST no grupo imposto."""
    grupo = localizar_grupo_tributo(imposto, "COFINS")
    if grupo is not None:
        return grupo
    return primeiro_filho(imposto, "COFINSST")


def extrair_cst_csosn(grupo_icms: Optional[ET.Element]) -> str:
    """Extrai CST ou CSOSN do grupo de ICMS."""
    cst = texto(grupo_icms, "CST")
    csosn = texto(grupo_icms, "CSOSN")
    return cst or csosn


def calcular_valor_produto(qtrib: str, vuntrib: str, vprod: str) -> Optional[Decimal]:
    """Usa vProd do XML; se não existir, calcula qTrib * vUnTrib."""
    vprod_dec = para_decimal(vprod)
    if vprod_dec is not None:
        return vprod_dec

    qtrib_dec = para_decimal(qtrib)
    vuntrib_dec = para_decimal(vuntrib)
    if qtrib_dec is None or vuntrib_dec is None:
        return None

    return qtrib_dec * vuntrib_dec


def calcular_base_pis_cofins(valor_produto: Optional[Decimal], vicms: str) -> Optional[Decimal]:
    """Critério usado na tela: Base PIS/COFINS calculada = Valor produto - vICMS."""
    if valor_produto is None:
        return None

    vicms_dec = para_decimal(vicms) or Decimal("0")
    return valor_produto - vicms_dec


def parsear_xml_nfe(
    conteudo_xml: bytes | str,
    nome_arquivo: str = "",
    criterio_referencia_icms: str = CRITERIO_REFERENCIA_PADRAO,
) -> list[dict]:
    """Lê um XML de NF-e e retorna uma lista de itens extraídos.

    O XML original não é modificado. A leitura é feita apenas em memória.
    """
    raiz = ET.fromstring(conteudo_xml)
    inf_nfe = localizar_inf_nfe(raiz)
    if inf_nfe is None:
        raise ValueError("Não foi encontrada a tag infNFe no XML.")

    ide = primeiro_filho(inf_nfe, "ide")
    emit = primeiro_filho(inf_nfe, "emit")

    numero_nf = texto(ide, "nNF")
    data_emissao = texto(ide, "dhEmi") or texto(ide, "dEmi")
    chave = extrair_chave(inf_nfe, raiz)
    cnpj_emitente = texto(emit, "CNPJ") or texto(emit, "CPF")
    nome_emitente = texto(emit, "xNome")
    descricao_criterio = descricao_criterio_referencia_icms(criterio_referencia_icms)

    linhas: list[dict] = []

    for det in todos_filhos(inf_nfe, "det"):
        produto = primeiro_filho(det, "prod")
        imposto = primeiro_filho(det, "imposto")
        grupo_icms = localizar_grupo_icms(imposto)
        grupo_pis = localizar_grupo_pis(imposto)
        grupo_cofins = localizar_grupo_cofins(imposto)

        qtrib = texto(produto, "qTrib")
        vuntrib = texto(produto, "vUnTrib")
        vprod = texto(produto, "vProd", "0") or "0"
        vfrete = texto(produto, "vFrete", "0") or "0"
        vseg = texto(produto, "vSeg", "0") or "0"
        voutro = texto(produto, "vOutro", "0") or "0"
        vdesc = texto(produto, "vDesc", "0") or "0"

        vbc = texto(grupo_icms, "vBC")
        picms = texto(grupo_icms, "pICMS")
        vicms = texto(grupo_icms, "vICMS")
        predbc_xml = texto(grupo_icms, "pRedBC")

        valor_referencia_icms = calcular_valor_referencia_icms(
            qtrib=qtrib,
            vuntrib=vuntrib,
            vprod=vprod,
            vfrete=vfrete,
            vseg=vseg,
            voutro=voutro,
            vdesc=vdesc,
            criterio=criterio_referencia_icms,
        )
        predbc_calculado = calcular_predbc(
            vbc=vbc,
            valor_referencia_icms=valor_referencia_icms,
        )

        valor_produto = calcular_valor_produto(qtrib=qtrib, vuntrib=vuntrib, vprod=vprod)
        base_pis_cofins_calculada = calcular_base_pis_cofins(
            valor_produto=valor_produto,
            vicms=vicms,
        )

        linhas.append(
            {
                "Arquivo XML": nome_arquivo,
                "Número NF": numero_nf,
                "Chave de acesso": chave,
                "Data emissão": data_emissao,
                "CNPJ emitente": cnpj_emitente,
                "Nome emitente": nome_emitente,
                "Número item": det.attrib.get("nItem", ""),
                "Código produto XML": texto(produto, "cProd"),
                "EAN/GTIN": texto(produto, "cEAN") or texto(produto, "cEANTrib"),
                "Descrição produto": texto(produto, "xProd"),
                "NCM": texto(produto, "NCM"),
                "CFOP": texto(produto, "CFOP"),
                "CST/CSOSN ICMS": extrair_cst_csosn(grupo_icms),
                "CST PIS XML": texto(grupo_pis, "CST"),
                "CST COFINS XML": texto(grupo_cofins, "CST"),
                "qTrib": float(para_decimal(qtrib))
                if para_decimal(qtrib) is not None
                else None,
                "vUnTrib": float(para_decimal(vuntrib))
                if para_decimal(vuntrib) is not None
                else None,
                "Valor produto": decimal_para_float(valor_produto),
                "vProd": decimal_2_para_float(vprod),
                "vFrete": decimal_2_para_float(vfrete),
                "vSeg": decimal_2_para_float(vseg),
                "vDesc": decimal_2_para_float(vdesc),
                "vOutro": decimal_2_para_float(voutro),
                "Valor referência ICMS": decimal_para_float(valor_referencia_icms),
                "Critério referência ICMS": descricao_criterio,
                "vBC": decimal_2_para_float(vbc),
                "pICMS": decimal_2_para_float(picms),
                "vICMS": decimal_2_para_float(vicms),
                "Base PIS/COFINS calculada": decimal_para_float(
                    base_pis_cofins_calculada
                ),
                "Base PIS XML": decimal_2_para_float(texto(grupo_pis, "vBC")),
                "Alíquota PIS XML": decimal_2_para_float(texto(grupo_pis, "pPIS")),
                "Valor PIS XML": decimal_2_para_float(texto(grupo_pis, "vPIS")),
                "Base COFINS XML": decimal_2_para_float(texto(grupo_cofins, "vBC")),
                "Alíquota COFINS XML": decimal_2_para_float(
                    texto(grupo_cofins, "pCOFINS")
                ),
                "Valor COFINS XML": decimal_2_para_float(
                    texto(grupo_cofins, "vCOFINS")
                ),
                "pRedBC XML": decimal_4_para_float(predbc_xml),
                "pRedBC calculado": float(predbc_calculado)
                if isinstance(predbc_calculado, Decimal)
                else None,
            }
        )

    return linhas


def parsear_varios_xmls(
    arquivos: Iterable,
    criterio_referencia_icms: str = CRITERIO_REFERENCIA_PADRAO,
) -> list[dict]:
    """Lê vários arquivos enviados pelo Streamlit."""
    resultado: list[dict] = []

    for arquivo in arquivos:
        conteudo = arquivo.getvalue()
        nome_arquivo = getattr(arquivo, "name", "")
        resultado.extend(
            parsear_xml_nfe(
                conteudo,
                nome_arquivo=nome_arquivo,
                criterio_referencia_icms=criterio_referencia_icms,
            )
        )

    return resultado
