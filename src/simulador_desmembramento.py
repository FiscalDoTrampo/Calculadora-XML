from decimal import Decimal
from typing import Any, Dict, Optional

from .calculos import (
    CRITERIO_REFERENCIA_PADRAO,
    arredondar_2,
    arredondar_4,
    calcular_predbc,
    calcular_valor_referencia_icms,
    descricao_criterio_referencia_icms,
    para_decimal,
)


def calcular_valor_tributo(
    base: Optional[Decimal], aliquota: Optional[Decimal]
) -> Optional[Decimal]:
    """
    Calcula PIS/COFINS quando o valor do XML não vier preenchido.

    Fórmula:
    valor = base * aliquota / 100
    """
    if base is None or aliquota is None:
        return None

    return (base * aliquota) / Decimal("100")


def valor_float_ou_none(valor: Optional[Decimal], casas: int = 2) -> Optional[float]:
    if valor is None:
        return None

    if casas == 4:
        return float(arredondar_4(valor))

    return float(arredondar_2(valor))


def obter_decimal_item(
    item_original: Dict[str, Any],
    coluna: str,
    padrao: Decimal = Decimal("0"),
) -> Decimal:
    valor = para_decimal(item_original.get(coluna))
    if valor is None:
        return padrao
    return valor


def obter_valor_produto_original(
    item_original: Dict[str, Any],
    quantidade_original: Decimal,
    vuntrib: Decimal,
) -> Decimal:
    """
    Usa o Valor produto extraído do XML.
    Se ele não existir, calcula pela quantidade original * vUnTrib.
    """
    valor_produto_original = para_decimal(item_original.get("Valor produto"))

    if valor_produto_original is not None:
        return valor_produto_original

    return quantidade_original * vuntrib


def montar_linha_simulada(
    item_original: Dict[str, Any],
    tipo: str,
    quantidade: Decimal,
    quantidade_original: Decimal,
    criterio_referencia_icms: str = CRITERIO_REFERENCIA_PADRAO,
) -> Dict[str, Any]:

    fator = quantidade / quantidade_original

    vuntrib = obter_decimal_item(item_original, "vUnTrib")
    vprod_original = obter_decimal_item(item_original, "vProd")
    vfrete_original = obter_decimal_item(item_original, "vFrete")
    vseg_original = obter_decimal_item(item_original, "vSeg")
    voutro_original = obter_decimal_item(item_original, "vOutro")
    vdesc_original = obter_decimal_item(item_original, "vDesc")
    vbc_original = obter_decimal_item(item_original, "vBC")
    vicms_original = obter_decimal_item(item_original, "vICMS")
    picms = obter_decimal_item(item_original, "pICMS")
    predbc_xml = para_decimal(item_original.get("pRedBC XML"))

    valor_produto_original = obter_valor_produto_original(
        item_original=item_original,
        quantidade_original=quantidade_original,
        vuntrib=vuntrib,
    )

    valor_produto = valor_produto_original * fator
    vprod = vprod_original * fator
    vfrete = vfrete_original * fator
    vseg = vseg_original * fator
    voutro = voutro_original * fator
    vdesc = vdesc_original * fator

    valor_referencia_icms = calcular_valor_referencia_icms(
        qtrib=quantidade,
        vuntrib=vuntrib,
        vprod=vprod,
        vfrete=vfrete,
        vseg=vseg,
        voutro=voutro,
        vdesc=vdesc,
        criterio=criterio_referencia_icms,
    )

    vbc = vbc_original * fator
    vicms = vicms_original * fator

    base_pis_cofins_calculada_original = (
        para_decimal(item_original.get("Base PIS/COFINS calculada"))
        or (valor_produto_original - vicms_original)
    )
    base_pis_cofins_calculada = base_pis_cofins_calculada_original * fator

    # Campos vindos do XML original
    base_pis_xml_original = para_decimal(item_original.get("Base PIS XML"))
    ppis_xml = para_decimal(item_original.get("Alíquota PIS XML"))
    vpis_xml_original = para_decimal(item_original.get("Valor PIS XML"))

    base_cofins_xml_original = para_decimal(item_original.get("Base COFINS XML"))
    pcofins_xml = para_decimal(item_original.get("Alíquota COFINS XML"))
    vcofins_xml_original = para_decimal(item_original.get("Valor COFINS XML"))

    # Se o XML não trouxe base de PIS/COFINS, usa a base calculada do item original.
    if base_pis_xml_original is None:
        base_pis_xml_original = base_pis_cofins_calculada_original

    if base_cofins_xml_original is None:
        base_cofins_xml_original = base_pis_cofins_calculada_original

    base_pis_xml = base_pis_xml_original * fator
    base_cofins_xml = base_cofins_xml_original * fator

    # Valor PIS proporcional:
    # 1. Usa valor do XML proporcional se existir
    # 2. Senão calcula pela base proporcional * alíquota / 100
    if vpis_xml_original is not None:
        vpis_xml = vpis_xml_original * fator
    else:
        vpis_xml = calcular_valor_tributo(base_pis_xml, ppis_xml)

    # Valor COFINS proporcional:
    # 1. Usa valor do XML proporcional se existir
    # 2. Senão calcula pela base proporcional * alíquota / 100
    if vcofins_xml_original is not None:
        vcofins_xml = vcofins_xml_original * fator
    else:
        vcofins_xml = calcular_valor_tributo(base_cofins_xml, pcofins_xml)

    predbc_calculado = calcular_predbc(
        vbc=vbc,
        valor_referencia_icms=valor_referencia_icms,
    )
    descricao_criterio = descricao_criterio_referencia_icms(criterio_referencia_icms)

    return {
        "Tipo": tipo,
        "Número NF": item_original.get("Número NF"),
        "Chave de acesso": item_original.get("Chave de acesso"),
        "Número item": item_original.get("Número item"),
        "Código produto XML": item_original.get("Código produto XML"),
        "Descrição produto": item_original.get("Descrição produto"),
        "NCM": item_original.get("NCM"),
        "CFOP": item_original.get("CFOP"),
        "CST/CSOSN ICMS": item_original.get("CST/CSOSN ICMS"),
        "CST PIS XML": item_original.get("CST PIS XML"),
        "CST COFINS XML": item_original.get("CST COFINS XML"),
        "Quantidade": float(arredondar_4(quantidade)),
        "vUnTrib": float(arredondar_4(vuntrib)),
        "Valor produto": float(arredondar_2(valor_produto)),
        "vProd proporcional": float(arredondar_2(vprod)),
        "vFrete proporcional": float(arredondar_2(vfrete)),
        "vSeg proporcional": float(arredondar_2(vseg)),
        "vDesc proporcional": float(arredondar_2(vdesc)),
        "vOutro proporcional": float(arredondar_2(voutro)),
        "Valor referência ICMS": valor_float_ou_none(valor_referencia_icms),
        "Critério referência ICMS": descricao_criterio,
        "vBC": float(arredondar_2(vbc)),
        "pICMS": float(arredondar_2(picms)),
        "vICMS": float(arredondar_2(vicms)),
        "Base PIS/COFINS calculada": float(arredondar_2(base_pis_cofins_calculada)),
        "Base PIS XML proporcional": valor_float_ou_none(base_pis_xml),
        "Alíquota PIS XML": valor_float_ou_none(ppis_xml),
        "Valor PIS XML proporcional": valor_float_ou_none(vpis_xml),
        "Base COFINS XML proporcional": valor_float_ou_none(base_cofins_xml),
        "Alíquota COFINS XML": valor_float_ou_none(pcofins_xml),
        "Valor COFINS XML proporcional": valor_float_ou_none(vcofins_xml),
        "pRedBC XML": float(arredondar_4(predbc_xml))
        if predbc_xml is not None
        else None,
        "pRedBC calculado": float(predbc_calculado)
        if predbc_calculado is not None
        else None,
    }


def simular_desmembramento(
    item_original: Dict[str, Any],
    quantidade_desmembrada,
    criterio_referencia_icms: str = CRITERIO_REFERENCIA_PADRAO,
) -> list[Dict[str, Any]]:

    quantidade_original = para_decimal(item_original.get("qTrib"))
    quantidade_desmembrada = para_decimal(quantidade_desmembrada)

    if quantidade_original is None or quantidade_original <= 0:
        raise ValueError("Quantidade original inválida.")

    if quantidade_desmembrada is None or quantidade_desmembrada <= 0:
        raise ValueError("Quantidade desmembrada precisa ser maior que zero.")

    if quantidade_desmembrada > quantidade_original:
        raise ValueError(
            "Quantidade desmembrada não pode ser maior que a quantidade original."
        )

    quantidade_restante = quantidade_original - quantidade_desmembrada

    linhas = []

    linhas.append(
        montar_linha_simulada(
            item_original=item_original,
            tipo="DESMEMBRADO",
            quantidade=quantidade_desmembrada,
            quantidade_original=quantidade_original,
            criterio_referencia_icms=criterio_referencia_icms,
        )
    )

    if quantidade_restante > 0:
        linhas.append(
            montar_linha_simulada(
                item_original=item_original,
                tipo="RESTANTE",
                quantidade=quantidade_restante,
                quantidade_original=quantidade_original,
                criterio_referencia_icms=criterio_referencia_icms,
            )
        )

    return linhas
