from __future__ import annotations

from decimal import Decimal
from typing import Optional

from .calculos import arredondar_2, arredondar_4, para_decimal

CEM = Decimal("100")
ZERO = Decimal("0")

ALIQUOTAS_ICMS_SUGERIDAS = {
    "ICMS 19%": Decimal("19"),
    "ICMS 17%": Decimal("17"),
}

ALIQUOTAS_PIS_COFINS_SUGERIDAS = {
    "Não cumulativo - PIS 1,65% / COFINS 7,60%": {
        "pis": Decimal("1.65"),
        "cofins": Decimal("7.60"),
    },
    "Cumulativo - PIS 0,65% / COFINS 3,00%": {
        "pis": Decimal("0.65"),
        "cofins": Decimal("3.00"),
    },
}


class CalculoManualInvalido(ValueError):
    """Erro para entradas manuais inválidas ou insuficientes."""


def decimal_manual(valor, padrao: Optional[Decimal] = ZERO) -> Optional[Decimal]:
    """
    Converte campo manual para Decimal.
    Aceita número com vírgula ou ponto.
    """
    valor_decimal = para_decimal(valor)

    if valor_decimal is None:
        return padrao

    return valor_decimal


def resolver_aliquota_icms(sugestao_icms: str, aliquota_icms_manual) -> Decimal:
    """Usa alíquota manual quando informada; senão usa a sugestão escolhida."""
    aliquota_manual = para_decimal(aliquota_icms_manual)

    if aliquota_manual is not None:
        return aliquota_manual

    return ALIQUOTAS_ICMS_SUGERIDAS.get(sugestao_icms, ZERO)


def resolver_aliquotas_pis_cofins(
    sugestao_pis_cofins: str,
    aliquota_pis_manual,
    aliquota_cofins_manual,
) -> tuple[Decimal, Decimal]:
    """Usa alíquotas manuais quando informadas; senão usa a sugestão escolhida."""
    aliquota_pis = para_decimal(aliquota_pis_manual)
    aliquota_cofins = para_decimal(aliquota_cofins_manual)

    sugestao = ALIQUOTAS_PIS_COFINS_SUGERIDAS.get(sugestao_pis_cofins, {})

    if aliquota_pis is None:
        aliquota_pis = sugestao.get("pis", ZERO)

    if aliquota_cofins is None:
        aliquota_cofins = sugestao.get("cofins", ZERO)

    return aliquota_pis, aliquota_cofins


def aplicar_percentual(base: Decimal, percentual: Decimal) -> Decimal:
    """Calcula base * percentual / 100."""
    return (base * percentual) / CEM




def calcular_icms_reducao_manual(
    valor_referencia_icms,
    reducao_icms,
    sugestao_icms: str,
    aliquota_icms_manual,
) -> dict:
    """Calcula ICMS com possível redução de base de cálculo."""
    valor_referencia = decimal_manual(valor_referencia_icms, padrao=None)
    reducao = decimal_manual(reducao_icms)
    aliquota_icms = resolver_aliquota_icms(sugestao_icms, aliquota_icms_manual)

    if valor_referencia is None or valor_referencia <= ZERO:
        raise CalculoManualInvalido(
            "Informe um Valor referência ICMS maior que zero para calcular."
        )

    if reducao < ZERO:
        raise CalculoManualInvalido("A redução de ICMS não pode ser negativa.")

    if reducao > CEM:
        raise CalculoManualInvalido("A redução de ICMS não pode ser maior que 100%.")

    if aliquota_icms <= ZERO:
        raise CalculoManualInvalido("Informe uma Alíquota ICMS maior que zero.")

    percentual_base_reduzida = CEM - reducao
    base_icms = aplicar_percentual(valor_referencia, percentual_base_reduzida)
    valor_reducao = valor_referencia - base_icms
    valor_icms = aplicar_percentual(base_icms, aliquota_icms)
    aliquota_efetiva_icms = (valor_icms / valor_referencia) * CEM

    return {
        "Valor referência ICMS": arredondar_2(valor_referencia),
        "Redução ICMS %": arredondar_4(reducao),
        "Valor redução ICMS": arredondar_2(valor_reducao),
        "Base ICMS reduzida": arredondar_2(base_icms),
        "Alíquota ICMS %": arredondar_4(aliquota_icms),
        "Valor ICMS": arredondar_2(valor_icms),
        "Alíquota efetiva ICMS %": arredondar_4(aliquota_efetiva_icms),
    }


def calcular_ipi_manual(base_ipi, aliquota_ipi) -> dict:
    """Calcula IPI a partir de base e alíquota informadas manualmente."""
    base = decimal_manual(base_ipi, padrao=None)
    aliquota = decimal_manual(aliquota_ipi)

    if base is None or base < ZERO:
        raise CalculoManualInvalido("Informe uma Base IPI válida. O valor não pode ser negativo.")

    if aliquota < ZERO:
        raise CalculoManualInvalido("A alíquota de IPI não pode ser negativa.")

    valor_ipi = aplicar_percentual(base, aliquota)
    total_com_ipi = base + valor_ipi

    return {
        "Base IPI": arredondar_2(base),
        "Alíquota IPI %": arredondar_4(aliquota),
        "Valor IPI": arredondar_2(valor_ipi),
        "Total com IPI": arredondar_2(total_com_ipi),
    }


def calcular_pis_cofins_manual(
    sugestao_pis_cofins: str,
    base_pis_cofins,
    aliquota_pis_manual,
    aliquota_cofins_manual,
) -> dict:
    """Calcula PIS e COFINS a partir de base e alíquotas manuais ou sugeridas."""
    base = decimal_manual(base_pis_cofins, padrao=None)
    aliquota_pis, aliquota_cofins = resolver_aliquotas_pis_cofins(
        sugestao_pis_cofins=sugestao_pis_cofins,
        aliquota_pis_manual=aliquota_pis_manual,
        aliquota_cofins_manual=aliquota_cofins_manual,
    )

    if base is None or base < ZERO:
        raise CalculoManualInvalido("Informe uma Base PIS/COFINS válida. O valor não pode ser negativo.")

    if aliquota_pis < ZERO or aliquota_cofins < ZERO:
        raise CalculoManualInvalido("As alíquotas de PIS/COFINS não podem ser negativas.")

    valor_pis = aplicar_percentual(base, aliquota_pis)
    valor_cofins = aplicar_percentual(base, aliquota_cofins)
    total_pis_cofins = valor_pis + valor_cofins

    return {
        "Base PIS/COFINS": arredondar_2(base),
        "Alíquota PIS %": arredondar_4(aliquota_pis),
        "Valor PIS": arredondar_2(valor_pis),
        "Alíquota COFINS %": arredondar_4(aliquota_cofins),
        "Valor COFINS": arredondar_2(valor_cofins),
        "Total PIS/COFINS": arredondar_2(total_pis_cofins),
    }


def calcular_reducao_por_valor_icms(
    valor_total_produto,
    valor_icms,
    sugestao_icms: str,
    aliquota_icms_manual,
) -> dict:
    """
    Calcula a alíquota efetiva e a redução equivalente a partir do ICMS informado.

    Fórmulas:
    - Alíquota efetiva = (Valor ICMS / Valor total produto) * 100
    - Base ICMS estimada = Valor ICMS / (Alíquota ICMS nominal / 100)
    - pRedBC equivalente = 100 - ((Base ICMS estimada / Valor total produto) * 100)

    Observação: a diferença simples entre a alíquota nominal e a efetiva é medida
    em pontos percentuais. O pRedBC fiscal equivalente é a redução da base de
    cálculo necessária para que a alíquota nominal resulte no ICMS informado.
    """
    valor_total = decimal_manual(valor_total_produto, padrao=None)
    icms = decimal_manual(valor_icms, padrao=None)
    aliquota_nominal = resolver_aliquota_icms(sugestao_icms, aliquota_icms_manual)

    if valor_total is None or valor_total <= ZERO:
        raise CalculoManualInvalido(
            "Informe um Valor total do produto maior que zero para calcular."
        )

    if icms is None or icms < ZERO:
        raise CalculoManualInvalido(
            "Informe um Valor do ICMS válido. O valor não pode ser negativo."
        )

    if aliquota_nominal <= ZERO:
        raise CalculoManualInvalido(
            "Informe uma Alíquota ICMS nominal maior que zero."
        )

    aliquota_efetiva = (icms / valor_total) * CEM
    base_icms_estimativa = icms / (aliquota_nominal / CEM)
    percentual_base_equivalente = (base_icms_estimativa / valor_total) * CEM
    predbc_equivalente = CEM - percentual_base_equivalente
    reducao_pontos_percentuais = aliquota_nominal - aliquota_efetiva

    if predbc_equivalente < ZERO:
        situacao = "ICMS informado acima da alíquota nominal"
    elif predbc_equivalente == ZERO:
        situacao = "Sem redução de base"
    else:
        situacao = "Com redução de base"

    return {
        "Valor total produto": arredondar_2(valor_total),
        "Valor ICMS informado": arredondar_2(icms),
        "Alíquota ICMS nominal %": arredondar_4(aliquota_nominal),
        "Alíquota efetiva ICMS %": arredondar_4(aliquota_efetiva),
        "Redução da alíquota em p.p.": arredondar_4(reducao_pontos_percentuais),
        "Base ICMS estimada": arredondar_2(base_icms_estimativa),
        "Percentual da base equivalente %": arredondar_4(percentual_base_equivalente),
        "pRedBC equivalente %": arredondar_4(predbc_equivalente),
        "Situação": situacao,
    }


def calcular_calculos_manuais(
    valor_referencia_icms,
    reducao_icms,
    sugestao_icms: str,
    aliquota_icms_manual,
    base_ipi,
    aliquota_ipi,
    sugestao_pis_cofins: str,
    base_pis_cofins,
    aliquota_pis_manual,
    aliquota_cofins_manual,
) -> dict:
    """
    Calcula ICMS, redução de base, IPI, PIS e COFINS a partir de campos manuais.

    Regras principais:
    - Base ICMS reduzida = Valor referência ICMS * (1 - Redução / 100)
    - ICMS = Base ICMS reduzida * Alíquota ICMS / 100
    - IPI = Base IPI * Alíquota IPI / 100
    - Base PIS/COFINS, quando vazia, usa Valor referência ICMS - ICMS
    """
    valor_referencia = decimal_manual(valor_referencia_icms, padrao=None)

    if valor_referencia is None or valor_referencia <= ZERO:
        raise CalculoManualInvalido(
            "Informe um Valor referência ICMS maior que zero para calcular."
        )

    reducao = decimal_manual(reducao_icms)
    aliquota_icms = resolver_aliquota_icms(sugestao_icms, aliquota_icms_manual)
    aliquota_ipi_dec = decimal_manual(aliquota_ipi)

    if reducao < ZERO:
        raise CalculoManualInvalido("A redução de ICMS não pode ser negativa.")

    if reducao > CEM:
        raise CalculoManualInvalido("A redução de ICMS não pode ser maior que 100%.")

    if aliquota_icms < ZERO or aliquota_ipi_dec < ZERO:
        raise CalculoManualInvalido("As alíquotas não podem ser negativas.")

    percentual_base_reduzida = CEM - reducao
    base_icms = aplicar_percentual(valor_referencia, percentual_base_reduzida)
    valor_reducao = valor_referencia - base_icms
    valor_icms = aplicar_percentual(base_icms, aliquota_icms)
    aliquota_efetiva_icms = (valor_icms / valor_referencia) * CEM

    base_ipi_dec = decimal_manual(base_ipi, padrao=valor_referencia)
    valor_ipi = aplicar_percentual(base_ipi_dec, aliquota_ipi_dec)

    aliquota_pis, aliquota_cofins = resolver_aliquotas_pis_cofins(
        sugestao_pis_cofins=sugestao_pis_cofins,
        aliquota_pis_manual=aliquota_pis_manual,
        aliquota_cofins_manual=aliquota_cofins_manual,
    )

    if aliquota_pis < ZERO or aliquota_cofins < ZERO:
        raise CalculoManualInvalido("As alíquotas de PIS/COFINS não podem ser negativas.")

    base_pis_cofins_dec = decimal_manual(
        base_pis_cofins,
        padrao=valor_referencia - valor_icms,
    )

    if base_pis_cofins_dec < ZERO:
        raise CalculoManualInvalido("A base de PIS/COFINS não pode ser negativa.")

    valor_pis = aplicar_percentual(base_pis_cofins_dec, aliquota_pis)
    valor_cofins = aplicar_percentual(base_pis_cofins_dec, aliquota_cofins)

    total_pis_cofins = valor_pis + valor_cofins
    total_tributos_calculados = valor_icms + valor_ipi + total_pis_cofins
    total_com_ipi = valor_referencia + valor_ipi

    return {
        "Valor referência ICMS": arredondar_2(valor_referencia),
        "Redução ICMS %": arredondar_4(reducao),
        "Valor redução ICMS": arredondar_2(valor_reducao),
        "Base ICMS reduzida": arredondar_2(base_icms),
        "Alíquota ICMS %": arredondar_4(aliquota_icms),
        "Valor ICMS": arredondar_2(valor_icms),
        "Alíquota efetiva ICMS %": arredondar_4(aliquota_efetiva_icms),
        "Base IPI": arredondar_2(base_ipi_dec),
        "Alíquota IPI %": arredondar_4(aliquota_ipi_dec),
        "Valor IPI": arredondar_2(valor_ipi),
        "Total com IPI": arredondar_2(total_com_ipi),
        "Base PIS/COFINS": arredondar_2(base_pis_cofins_dec),
        "Alíquota PIS %": arredondar_4(aliquota_pis),
        "Valor PIS": arredondar_2(valor_pis),
        "Alíquota COFINS %": arredondar_4(aliquota_cofins),
        "Valor COFINS": arredondar_2(valor_cofins),
        "Total PIS/COFINS": arredondar_2(total_pis_cofins),
        "Total tributos calculados": arredondar_2(total_tributos_calculados),
    }
