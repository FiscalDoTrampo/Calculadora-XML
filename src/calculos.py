from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

DUAS_CASAS = Decimal("0.01")
QUATRO_CASAS = Decimal("0.0001")

CRITERIO_REFERENCIA_PADRAO = "valor_operacao"

DESCRICOES_CRITERIO_REFERENCIA_ICMS = {
    "quantidade_unitario": "Quantidade x unitário + vOutro",
    "valor_operacao": "Valor da operação",
    "somente_vprod": "Somente vProd",
}


class CriterioReferenciaICMSInvalido(ValueError):
    """Erro usado quando o critério de referência ICMS não é reconhecido."""


def para_decimal(valor) -> Optional[Decimal]:
    """
    Converte valores do XML para Decimal.
    Aceita valores com ponto ou vírgula.
    Retorna None quando o valor não existe ou está vazio.
    """
    if valor is None:
        return None

    valor_texto = str(valor).strip()

    if valor_texto == "" or valor_texto.lower() == "nan":
        return None

    try:
        return Decimal(valor_texto.replace(",", "."))
    except InvalidOperation:
        return None


def decimal_ou_zero(valor) -> Decimal:
    """Converte para Decimal; quando ausente/inválido, retorna zero."""
    return para_decimal(valor) or Decimal("0")


def arredondar_2(valor: Optional[Decimal]) -> Optional[Decimal]:
    """
    Arredonda para 2 casas decimais.
    Usado para campos monetários e percentuais vindos do XML.
    """
    if valor is None:
        return None

    return valor.quantize(DUAS_CASAS, rounding=ROUND_HALF_UP)


def arredondar_4(valor: Optional[Decimal]) -> Optional[Decimal]:
    """
    Arredonda para 4 casas decimais.
    Usado para exibir o pRedBC calculado com mais precisão.
    """
    if valor is None:
        return None

    return valor.quantize(QUATRO_CASAS, rounding=ROUND_HALF_UP)


def normalizar_criterio_referencia_icms(criterio: Optional[str]) -> str:
    """Retorna um critério válido ou o critério padrão do projeto."""
    criterio_normalizado = (criterio or CRITERIO_REFERENCIA_PADRAO).strip()

    if criterio_normalizado not in DESCRICOES_CRITERIO_REFERENCIA_ICMS:
        raise CriterioReferenciaICMSInvalido(
            f"Critério de referência ICMS inválido: {criterio_normalizado}"
        )

    return criterio_normalizado


def descricao_criterio_referencia_icms(criterio: Optional[str]) -> str:
    """Retorna a descrição visível do critério de Valor referência ICMS."""
    criterio_normalizado = normalizar_criterio_referencia_icms(criterio)
    return DESCRICOES_CRITERIO_REFERENCIA_ICMS[criterio_normalizado]


def calcular_valor_referencia_icms(
    qtrib,
    vuntrib,
    vprod,
    vfrete,
    vseg,
    voutro,
    vdesc,
    criterio,
) -> Optional[Decimal]:
    """
    Calcula o Valor referência ICMS usado no cálculo do pRedBC calculado.

    Critérios aceitos:
    - quantidade_unitario: (qTrib * vUnTrib) + vOutro
    - valor_operacao: vProd + vFrete + vSeg + vOutro - vDesc
    - somente_vprod: vProd
    """
    criterio_normalizado = normalizar_criterio_referencia_icms(criterio)

    qtrib_dec = para_decimal(qtrib)
    vuntrib_dec = para_decimal(vuntrib)
    vprod_dec = decimal_ou_zero(vprod)
    vfrete_dec = decimal_ou_zero(vfrete)
    vseg_dec = decimal_ou_zero(vseg)
    voutro_dec = decimal_ou_zero(voutro)
    vdesc_dec = decimal_ou_zero(vdesc)

    if criterio_normalizado == "quantidade_unitario":
        if qtrib_dec is None or vuntrib_dec is None:
            return None
        return (qtrib_dec * vuntrib_dec) + voutro_dec

    if criterio_normalizado == "valor_operacao":
        return vprod_dec + vfrete_dec + vseg_dec + voutro_dec - vdesc_dec

    if criterio_normalizado == "somente_vprod":
        return vprod_dec

    return None


def calcular_predbc(vbc, valor_referencia_icms) -> Optional[Decimal]:
    """
    Calcula o percentual de redução de base de ICMS.

    Fórmula:
    pRedBC calculado = 100 - ((vBC / Valor referência ICMS) * 100)
    """
    vbc_dec = para_decimal(vbc)
    valor_referencia_dec = para_decimal(valor_referencia_icms)

    if vbc_dec is None or valor_referencia_dec is None:
        return None

    if valor_referencia_dec <= 0:
        return None

    percentual = Decimal("100") - ((vbc_dec / valor_referencia_dec) * Decimal("100"))

    return arredondar_4(percentual)
