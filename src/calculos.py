from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

DUAS_CASAS = Decimal("0.01")
QUATRO_CASAS = Decimal("0.0001")


def para_decimal(valor) -> Optional[Decimal]:
    """
    Converte valores do XML para Decimal.
    Aceita valores com ponto ou vírgula.
    Retorna None quando o valor não existe ou está vazio.
    """
    if valor is None:
        return None

    valor_texto = str(valor).strip()

    if valor_texto == "":
        return None

    try:
        return Decimal(valor_texto.replace(",", "."))
    except InvalidOperation:
        return None


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


def calcular_predbc(qtrib, vuntrib, voutro, vbc) -> Optional[Decimal]:
    """
    Calcula o percentual de redução de base de ICMS.

    Fórmula:
    100 - ((vBC / ((qTrib * vUnTrib) + vOutro)) * 100)
    """

    qtrib_dec = para_decimal(qtrib)
    vuntrib_dec = para_decimal(vuntrib)
    voutro_dec = para_decimal(voutro)
    vbc_dec = para_decimal(vbc)

    if qtrib_dec is None or vuntrib_dec is None or vbc_dec is None:
        return None

    if voutro_dec is None:
        voutro_dec = Decimal("0")

    divisor = (qtrib_dec * vuntrib_dec) + voutro_dec

    if divisor == 0:
        return None

    percentual = Decimal("100") - ((vbc_dec / divisor) * Decimal("100"))

    return arredondar_4(percentual)
