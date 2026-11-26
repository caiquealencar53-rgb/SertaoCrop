# SertãoCrop

Plataforma local de simulação agrícola com **Python + Qt (PySide6) + AquaCrop-OSPy + Pandas + SQLite**.

A aplicação liga, de ponta a ponta, cadastros agrícolas → clima/solo/irrig → AquaCrop → Pandas → SQLite → interface Qt. **Nenhum resultado é calculado com dados aleatórios ou inventados**: quando a execução falha, o status `ERRO` é gravado e a tela mostra a mensagem real.

---

## 1. Requisitos

- Python 3.14 (testado com 3.14.9)
- AquaCrop-OSPy `3.1.0`
- PySide6 `6.12.0`
- pandas `3.1.1`, numpy `2.5.4`, matplotlib `3.11.2`
- spotpy `1.6.7` (calibração opcional)

Tudo está congelado em `requirements.txt`.

> **Não use Flet, Tkinter ou outro framework.** A interface é exclusivamente PySide6/Qt.

---

## 2. Instalação e execução

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

Depuração no VS Code: a configuração em `.vscode/launch.json` aponta para `main.py`.

O banco é criado automaticamente em `data_base/dados/sertaocrop.db` na primeira execução. O schema versionado é `database/schema.sql`; o arquivo `.db` nunca fica na raiz do projeto.

---

## 3. Testes

```bash
venv/bin/python -m unittest discover -s tests -v
```

Suíte separada por responsabilidade:

| Arquivo | O que cobre |
|---|---|
| `tests/test_database.py` | schema, integridade referencial, cadastros e repositórios |
| `tests/test_validation.py` | datas, clima, camadas de solo e irrigação |
| `tests/test_climate.py` | importação/persistência/ordem das colunas do clima |
| `tests/test_simulation.py` | execução real do AquaCrop, recuperação, histórico, milheto bloqueado |
| `tests/test_calibration.py` | restrições da calibração e declaração do spotpy |
| `tests/test_ui.py` | telas Qt em modo offscreen, sinais e `QThread` |

A simulação de integração roda Sorghum com a série de demonstração e confere produtividade, métricas e série diária gravadas no SQLite.

---

## 4. Arquitetura

```text
main.py                    entry point (PySide6)
config/                    caminhos e versão do AquaCrop
database/                  schema.sql + conexão + repositórios (únicos acessos ao SQLite)
services/                  validação, clima, solo, simulação e calibração
integracao_aquacrop/       adaptador da API real do AquaCrop + catálogo de culturas
frontand/                  janela, tema e telas (mvc-ish, sem regra de negócio na UI)
data/demo/                 série climática de demonstração (origem não documentada)
tests/                     testes automatizados
scripts/                   estudo didático da API preservado
```

Fluxo de uma simulação:

1. A tela `Nova simulação` lê somente registros do banco e valida o configuration.
2. `services/simulation_service.py` cria o registro `PENDENTE`/`EXECUTANDO`.
3. `integracao_aquacrop/adapter.py` monta `weather_df`, `Soil`, `Crop`, `InitialWaterContent` e `IrrigationManagement`, e chama `AquaCropModel.run_model()`.
4. `services/simulation_service.py` usa Pandas para converter as saídas reais em métricas e série diária.
5. `database/repositories.py` grava `resultados` e `crescimento_diario`, e marca `CONCLUIDA`.
6. As telas `Resultados` e `Histórico` leem tudo de volta do SQLite. A execução pesada roda em `QThread` com sinais/slots.

---

## 5. Banco de dados

- Fonte da estrutura: **`database/schema.sql`**.
- Arquivo ativo (único): **`data_base/dados/sertaocrop.db`**, criado automaticamente na primeira execução.
- As cópias legadas `data_base/sertaocrop.db` e `data_base/dados/sertaocrop_v2.db` foram removidas; nenhum `.db` fica na raiz.
- `data_base/conexao.py` e `data_base/criar_tabelas.py` agora são apenas shims de compatibilidade; os originais foram preservados como `data_base/conexao_original.py`.
- Chaves estrangeiras são ativadas em toda conexão; há índices para clima, simulações e crescimento.
- Cada simulação registra versão do AquaCrop, cultura, solo, estação, manejo, datas, condição inicial e `status`/`erro`. Os parâmetros culturais registrados guardam `fonte` e `validado`.

---

## 6. Dados climáticos

A tela `Clima` importa CSV/TXT. Colunas aceitas (case-insensitive; aliases entre parênteses):

| Campo obrigatório | Aliases |
|---|---|
| `data` | `Date` |
| `temperatura_min` | `Tmin`, `MinTemp` |
| `temperatura_max` | `Tmax`, `MaxTemp` |
| `precipitacao` | `Rain`, `Precipitation`, `Precip` |
| `eto` | `ETo`, `ET0`, `ReferenceET` |

Opcionais reconhecidos: `RH` → umidade relativa, `Wind` → velocidade do vento, `Rs` → radiação solar.

Regras validadas antes de salvar:

- série **diária contínua** (sem lacunas);
- datas únicas em `AAAA-MM-DD`;
- `0 < temperatura_min <= temperatura_max`;
- precipitação ≥ 0 e ETo > 0;
- o clima deve cobrir todo o período simulado.

O AquaCrop lê clima **por posição**, por isso `services/climate_service.py` produz sempre:

```text
MinTemp, MaxTemp, Precipitation, ReferenceET, Date
```

### Série de demonstração

`data/demo/clima_demo.csv` (366 dias de 2024) é uma cópia de `backand/models/climate_data_2024.csv`. **A origem e a validade científica não estão documentadas.** Ao importar pela tela, a estação recebe `eh_demonstracao = 1` e os registros `origem = DEMONSTRACAO`; o dashboard exibe aviso permanente. Não é dado do Semiárido Brasileiro validado.

---

## 7. Culturas e limitações científicas

| Cultura | Situação |
|---|---|
| **Sorgo** (`Sorghum`) | Simulação habilitada com os parâmetros embutidos do AquaCrop 3.1.0 (conjunto padrão FAO). **Não calibrado localmente.** |
| **Milheto** | Cadastrado, mas **simulação e calibração bloqueadas**: `aquacrop==3.1.0` não possui `Millet`/`PearlMillet` em `crop_params`. Nenhum parâmetro foi inventado. |

O catálogo de culturas suportadas é lido da própria biblioteca instalada (`aquacrop.entities.crop.crop_params`).

### Calibração

`services/calibration_service.py` mantém a funcionalidade SCE-UA/SpotPy do projeto original, agora para Sorghum. O resultado é gravado com `status = 'EXPERIMENTAL'` e a interface explicita que convergência do otimizador **não** equivale a validação científica. O script antigo `testes/teste.py` foi preservado como referência histórica, mas usava `Crop('Millet')` e produtividade observada fictícia; não é um teste válido.

### Métricas derivadas

`get_simulation_results()` do AquaCrop 3.1.0 não traz ET, biomassa final nem data por dia. A aplicação deriva essas grandezas das saídas reais:

- biomassa: `get_crop_growth()['biomass'] / 100` (g/m² → t/ha);
- ET: soma de `Es + Tr` de `get_water_flux()`;
- `Tr/TrPot`: razão diária média;
- datas: derivadas do contador de passos em relação à data de início da simulação.

Todas são sinalizadas na tela e no campo `observacoes` do banco como **derivadas**, não calibradas.

---

## 8. Interface

Telas com identidade verde/bege (`frontand/theme.py`):

- Visão geral, Cadastro agrícola (produtor → propriedade → área → experimento), Culturas, Clima, Solo, Irrigação, Nova simulação, Resultados, Histórico e Calibração.
- Botões de salvar/remover/importar/exportar estão ligados a repositórios ou serviços.
- Gráficos Matplotlib usam exclusivamente a série gravada no banco.
- Simulação e calibração rodam em `QThread`; mensagens de execução, sucesso e erro aparecem na própria tela.
- As telas usam área de rolagem, então formulários, botões e gráficos continuam acessíveis em janelas pequenas.
- `Nova simulação` já abre com Sorgo, um solo e Sequeiro pré-selecionados; o botão **Importar clima demo** importa a série de demonstração sem sair da tela. Escolhas feitas pelo usuário são preservadas ao recarregar a página.

---

## 9. Preservação do trabalho anterior

- `backand/engine/simulador.py` e `backand/models/main.ipynb` (alterações não commitadas) **não foram modificados**.
- O roteiro de estudo da API que estava em `main.py` está em `scripts/estudo_api_aquacrop.py` (usa o clima de Túnis embutido no pacote — apenas didático).
- A UI antiga com placeholders está em `frontand/legacy/`; `frontand/main_window/ui_main_window.py` agora redireciona para a janela funcional.
- `seaborn` foi removido de `requirements.txt` por não ser usado; `spotpy` foi adicionado porque a calibração o exige.

### Limpeza de escopo

Foram removidos apenas itens sem função, preservando o trabalho anterior listado acima:

- bytecode versionado (`__pycache__/` e `*.pyc`), regenerado automaticamente e agora ignorado pelo Git;
- arquivos vazios: `version`, `backand/models/dado_climatico.xls` e `testes/Clima_Serra.txt`;
- cópias antigas do banco (`sertaocrop.db` na raiz e `data_base/dados/sertaocrop_v2.db`);
- o diretório vazio `backand/services/`.

---

## 10. Como usar o fluxo mínimo

1. `Clima` → **Importar demonstração** (ou importe seu CSV medido). Se preferir, use **Importar clima demo** direto em `Nova simulação`.
2. `Solo` → use um perfil embutido do AquaCrop ou cadastre camadas com `th_wp < th_fc < th_s`.
3. `Irrigação` → escolha sequeiro, umidade, intervalo ou calendário.
4. `Nova simulação` → **Revisar parâmetros** e depois **Executar simulação**.
5. `Resultados` → métricas, gráfico e exportação CSV; `Histórico` → todas as execuções com status e erro.

Para resultados com valor científico, substitua a série de demonstração por dados medidos e documentados da área simulada e registre a origem de qualquer parâmetro calibrado.
