# Calculadora de redução de base ICMS em XML de NF-e

Projeto simplificado em Python/Streamlit para:

1. Fazer upload de um ou vários XMLs de NF-e.
2. Ler os itens da nota.
3. Extrair os principais campos fiscais do item.
4. Calcular o `pRedBC` com base nos valores do próprio XML.

## Fórmula utilizada

```text
pRedBC calculado = 100 - ((vBC / ((qTrib * vUnTrib) + vOutro)) * 100)
```

Onde:

- `vBC`: base de ICMS do item no XML.
- `qTrib`: quantidade tributável.
- `vUnTrib`: valor unitário tributável.
- `vOutro`: outras despesas do item. Quando não existir, será considerado `0`.

## Campos extraídos

- Arquivo XML
- Número NF
- Chave de acesso
- Data emissão
- CNPJ emitente
- Nome emitente
- Número item
- Código produto XML
- EAN/GTIN
- Descrição produto
- NCM
- CFOP
- CST/CSOSN ICMS
- qTrib
- vUnTrib
- vOutro
- vBC
- pICMS
- vICMS
- pRedBC XML
- pRedBC calculado

## Como rodar

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Usar o caminho direto da `.venv` evita o bloqueio do `Activate.ps1` no PowerShell.

## Observações

- O XML original não é alterado.
- O parser trata namespace padrão da NF-e.
- O cálculo evita divisão por zero.
- Percentuais e valores são arredondados para 2 casas decimais na saída.
