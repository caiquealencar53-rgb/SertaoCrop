# Dados de demonstração

`clima_demo.csv` é uma cópia de `backand/models/climate_data_2024.csv`, presente no
projeto original. **A origem e a validade científica dessa série não estão documentadas**;
ela serve apenas para demonstração da interface e para os testes de integração.

Não é dado do Semiárido Brasileiro validado, não deve ser usado em estudo científico
nem apresentado como resultado de campo. Ao importar, a estação é marcada como
`eh_demonstracao = 1` e a origem dos registros como `DEMONSTRACAO`.

Colunas: `Date,Year,Month,Day,DOY,Tmin,Tmax,Tmean,Rain,ETo,RH,Wind,Rs` (diária).
