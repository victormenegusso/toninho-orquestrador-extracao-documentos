# Revisao do projeto - v1

Atualizado em: 2026-03-29

## Contexto

O projeto esta de certa maneira funcional, mas ainda tem muitos bugs, melhorias e tech debt. O objetivo desta revisao e organizar tudo isso em um backlog estruturado, priorizado e com status atualizado. Assim, a equipe tem um roteiro claro para as proximas iteracoes de desenvolvimento.


## Funcionamentos a revisar

1 -> /processos/novo
1.1 -> avaliar o processo do campo "Formato de saída" pois tanto "Arquivo Unico" e "Multiplos arquivos" estão funcionando da mesma maneira, gerando um arquivo por execução. Verificar se é necessário corrigir isso ou se é apenas uma questão de nomenclatura. Confirme como esta implementado atualmente e se há alguma diferença real entre os dois modos.


## Melhorias na interface

1 -> /processos/{id}

1.1 -> no campo "Execuções Recentes" poderiamos ter uma maneira de abrir a execução listada, hoje eu preciso clicar em "ver todas" que me manda para "execucoes?processo_id={id}" e ai sim clicar na execução. Seria interessante ter um link direto para a execução ali, para agilizar o acesso.

## BUGS

1 -> http://localhost:8000/execucoes?processo_id={id}
1.1 -> nao parece estar filtrando as execucoes por processo_id, esta mostrando execucoes de outros processos. Verificar a query que esta sendo feita no backend e corrigir o filtro para garantir que apenas as execucoes do processo selecionado sejam exibidas.

2 -> execucoes/{id}/paginas
2.1 -> ao acessar a pagina, os campos "Total de páginas" e "extraídas com sucesso", "Erros"e "Tamanho Total" não estao corretos.

3 -> ainda esta tendo algum consumo de recursos, talvez banco, pois depois de fazer algumas navegacoes e execucoes, o sistema fica mais lento. Verificar os logs do banco de dados e do backend para identificar possíveis consultas lentas ou vazamentos de conexões que possam estar causando esse problema.

## observacoes

- estou sempre usando o docker, logo para testar vamos dar preferencia em "make docker-up" e "make docker-down" para garantir que o ambiente esteja limpo e consistente.

- para os testes de interface, podemos usar o cypress ou outro framework de testes end-to-end para automatizar a navegação e validação dos elementos na interface. Isso vai ajudar a garantir que as correções e melhorias sejam testadas de forma consistente.
